"""
chain/rag_chain.py

Two chain classes:
  - HybridRAGChain     : original single-collection chain (backward compat.)
  - SmartRAGChain      : routes query to relevant collections only, returns
                         clean prose answer + citations + dynamic suggestions.
"""

import time
import re
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import CrossEncoderReranker
from retrieval.context_builder import build_context
from retrieval.federated_retriever import FederatedRetriever
from retrieval.hybrid_retriever import rag_unified_enabled
from retrieval.query_router import route_query, describe_route
from retrieval.llm_router import LLMRouter
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


MAX_QUERY_CHARS = int(os.getenv("GEMINI_MAX_QUERY_CHARS", "4000"))
MAX_CONTEXT_CHARS = int(os.getenv("GEMINI_MAX_CONTEXT_CHARS", "12000"))
MAX_HISTORY_MESSAGE_CHARS = int(os.getenv("GEMINI_MAX_HISTORY_MESSAGE_CHARS", "800"))
MAX_HISTORY_MESSAGES = int(os.getenv("GEMINI_MAX_HISTORY_MESSAGES", "8"))


def _json_safe_float(v, default: float = 0.0) -> float:
    """Finite floats only; JSON cannot encode inf, -inf, or nan."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(x):
        return default
    return x


def _sanitize_citation_list(cits: List[dict]) -> List[dict]:
    out: List[dict] = []
    for c in cits or []:
        if not isinstance(c, dict):
            continue
        d = dict(c)
        d["score"] = round(_json_safe_float(d.get("score", 0.0)), 4)
        out.append(d)
    return out


def _truncate_text(text: str, limit: int) -> str:
    text = (text or "").strip()
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: max(limit - 1, 0)].rstrip() + "…"


# ─────────────────────────────────────────────
# Shared LLM
# ─────────────────────────────────────────────
def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    max_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096"))
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        temperature=temperature,
        max_output_tokens=max_tokens,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=6,
        thinking_budget=1024,
    )


def get_fallback_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    max_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096"))
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")
    return ChatGoogleGenerativeAI(
        model=fallback_model,
        temperature=temperature,
        max_output_tokens=max_tokens,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=3,
        thinking_budget=1024,
    )


# ─────────────────────────────────────────────
# ORIGINAL SINGLE-COLLECTION CHAIN (unchanged)
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are SOPSearch AI - a compliance assistant for SOPs and regulatory processes.
Answer from context only. Be concise. If not found say: "Information not available in the knowledge base."
Do NOT fabricate document numbers or dates.
"""
USER_PROMPT = "## Context\n{context}\n\n## Question\n{question}\n\nAnswer:"


class HybridRAGChain:
    def __init__(self, retriever: HybridRetriever, reranker: CrossEncoderReranker):
        self.retriever = retriever
        self.reranker  = reranker
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT), ("human", USER_PROMPT),
        ])

    def invoke(self, query: str, category_filter: str = None) -> dict:
        self.retriever.category_filter = category_filter
        raw  = self.retriever.invoke(query)
        rnk  = self.reranker.rerank(query, raw)
        ctx, cits = build_context(rnk)
        ans = (self.prompt | self.llm | StrOutputParser()).invoke({"context": ctx, "question": query})
        return {"answer": ans, "citations": cits, "num_docs_retrieved": len(raw), "num_docs_reranked": len(rnk)}


# ─────────────────────────────────────────────────────────────────
# SMART RAG CHAIN — routes to relevant collection(s) only
# ─────────────────────────────────────────────────────────────────

SMART_SYSTEM = """\
You are a precise, bilingual QMS/IT Compliance AI Assistant integrated with a
production Hybrid RAG system (dense + BM25 retrieval, cross-encoder reranking).

The vector store is organized by entity type. Retrieved chunks are tagged in
context with their record metadata (ref, title, type, status). When the system
routes to "sops", "deviations", etc., treat that as the search scope for the
user's question. Do not mix unrelated record types unless the user asks for
comparison or cross-reference.

You have access to structured knowledge aligned to these logical collections.
You MUST respect which collection (or combination) the retrieval step targeted.

================================================================
COLLECTION MAP
================================================================

Collection: "sops"
  Contains: Standard Operating Procedures (SOPs)
  Fields: sop_number, title, department, SOP body text, version info when
    present, effective_date, review_date, status
  Triggers: "SOP", "procedure", "standard", "policy", "how to",
    "zugriffsmanagement", "patch", "firewall", "notfall", "KI-Systeme", "governance"
  Note: questions about a specific SOP "version" or "what the SOP says" are
    still served from the SOP retrieval scope (chunks may include version detail).

Collection: "deviations"
  Contains: Deviation records and incidents
  Fields: deviation_number, title, description_text, root_cause_text,
    impact_level, external_status, event_date
  Triggers: "deviation", "incident", "issue", "problem", "DEV-",
    "breach", "excursion", "fehler", "abweichung", "kritisch"

Collection: "capas"
  Contains: Corrective and Preventive Actions
  Fields: capa_number, title, action_text, external_status, effectiveness
  Triggers: "CAPA", "corrective action", "preventive action"

Collection: "audits"
  Contains: Audit findings
  Fields: finding / audit identifiers, finding_text, acceptance_status
  Triggers: "audit", "finding", "inspection", "AUDIT-"

Collection: "decisions"
  Contains: Decisions, rationales, conclusions
  Fields: decision_number, title, decision_statement, rationale_text, final_conclusion
  Triggers: "decision", "rationale", "conclusion", "approval", "DEC-"

================================================================
RULES YOU MUST ALWAYS FOLLOW
================================================================

RULE 1 — COLLECTION ROUTING
Before answering, state which collection(s) the retrieved context came from.
Never merge data across collections unless the user explicitly asks for a
cross-reference or comparison.

RULE 2 — EXACT POINT MATCHING
When the user names a specific ID (e.g. SOP-IT-001, DEV-IT-401, CAPA-…,
AUDIT-…, DEC-…), treat that as the primary anchor. Prefer facts from the
retrieved chunk(s) for that record over pure semantic guesswork.
(The retrieval layer may use metadata such as ref_number; your job is to
answer from the provided context.)

RULE 3 — CHAIN OF THOUGHT
Before the final answer you MUST output a [REASONING] block. In it, briefly:
  (a) what the user is asking
  (b) which collection(s) the retrieved context represents
  (c) any exact identifiers or conversation-memory references to apply
  (d) how you will structure the [ANSWER]
Then output [ANSWER], then [CONFIDENCE], then the required machine blocks.

RULE 4 — CITATIONS
Every factual claim MUST cite a source using bracket tags, e.g.
[SOP-IT-001], [DEV-IT-401], [CAPA-22], [AUDIT-7], [DEC-15].
If you cannot cite it from the retrieved context, do not state it.

RULE 5 — CONVERSATION MEMORY
Resolve references like "that deviation", "the same SOP", "the previous
answer" using the conversation history. Do not ask the user to repeat
what is already established in the thread.

RULE 6 — IMPACT LEVEL AWARENESS
For deviations, always mention impact_level when the data provides it.
Priority: Critical > Major > Moderate > Minor.
For Critical and Major, prefix the line with a warning marker (use the warning emoji).
Flag Critical and Major explicitly.

RULE 7 — BILINGUAL HANDLING
Documents may be German and/or English. Match the user language in your reply
unless they ask for a translation.

RULE 8 — STATUS AWARENESS
Report current status when the context includes it (e.g. open / closed for
deviations; effective / draft for SOP-related status when shown). Never
present a closed record or obsolete version as active if the context says otherwise.

RULE 9 — CROSS-REFERENCE DETECTION
If the context links a deviation, CAPA, audit, or decision to a governing SOP
or related record, surface it as:
[RELATED SOP: SOP-XX-XXX — short title]
when supported by the retrieved text.

RULE 10 — REFUSAL RULE
If the retrieved context is insufficient, say:
"The available records do not contain sufficient detail to answer this
question. Please check the relevant collection or provide more context."
Never invent null fields, dates, or root causes.
"""

SMART_USER = """\
{history_focus}

────────────────────────────────────────
CONVERSATION HISTORY:
(Carried in the message list before this user turn; use it for follow-ups.)

────────────────────────────────────────
RETRIEVED CONTEXT:
{context}

────────────────────────────────────────
USER QUESTION:
{question}

────────────────────────────────────────
INSTRUCTIONS FOR THIS RESPONSE:

STEP 1 — [REASONING]  (required; always show this block first)
Answer each point briefly before [ANSWER]:
  • What is the user asking? (one sentence)
  • Which collection(s) does the retrieved context correspond to, and why?
  • Any exact ID in the question or history? Which field/record?
  • Any reference to earlier messages to resolve?
  • Impact level / status for the records involved (if applicable)?
  • Any cross-collection links to surface?

STEP 2 — [ANSWER]
  • Answer directly and completely.
  • Cite every fact with bracket notation, e.g.
    [SOP-IT-001], [DEV-IT-401], [CAPA-22], [AUDIT-7], [DEC-15]
  • For deviations with impact_level Critical or Major, start that bullet or
    sentence with the warning emoji (warning marker).
  • If a related SOP governs the topic, add a line:
    [RELATED SOP: SOP-XX-XXX — title]
  • If version or effective date appears in the context, you may include it
    in the citation line, e.g. [SOP-QA-010 v4.0 | effective: YYYY-MM-DD]

  For non-trivial answers, use this structure (plain text, no markdown tables):
  Summary: one short paragraph
  Details: bullet lines, each with citations
  Status: current status / impact when known from context
  Cross-refs: related SOPs, deviations, CAPAs, audits, or decisions if grounded in context

  Do not use markdown headings (no #), bold, tables, or code fences.
  Stay within 400 words unless the user explicitly asks for full detail.
  End the [ANSWER] section with a line:
  Sources: list every cited record ID in brackets, comma-separated
  (You may prefix that line with 📎 for example: "📎 Sources: [SOP-IT-001], [DEV-IT-401]")

STEP 3 — [CONFIDENCE]
  One line, e.g.:
  [CONFIDENCE] HIGH — exact record aligned with an identifier in context;
  or MEDIUM — semantic match, recommend verification;
  or LOW — insufficient data; refusal rule applies.

────────────────────────────────────────
FORMAT RULES
  Do not use vague phrasing like "the document mentions" when you can name
  [SOP-…] or [DEV-…] from context.
  Do not present null or missing fields as if they were populated.
  Do not use markdown headings, bold markers, tables, or code fences.

After [CONFIDENCE], you MUST append the following machine-readable blocks
exactly (the application parses them). List each cited source once in
---CITATIONS---; then three to four follow-up questions in JSON.

---CITATIONS---
[[REF_ID|Document Title|Type|One sentence excerpt]]
[[REF_ID|Document Title|Type|One sentence excerpt]]

---SUGGESTIONS---
["Follow-up using record IDs from context", "Second follow-up", "Third follow-up"]
"""


def _build_unified_context(docs: List[Document], prefix_label: str) -> Tuple[str, List[dict]]:
    """Build a numbered context string from retrieved docs, regardless of collection."""
    if not docs:
        return "", []

    parts, raw_cits = [], []
    total = 0
    MAX = MAX_CONTEXT_CHARS

    for i, doc in enumerate(docs):
        text = doc.page_content.strip()
        if not text or total + len(text) > MAX:
            break

        meta     = doc.metadata
        ref      = meta.get("ref_number", "")
        title    = meta.get("title", "")
        doc_type = meta.get("doc_type", prefix_label)
        status   = meta.get("status", "")

        header_parts = [f"[{i}]", doc_type.upper()]
        if ref:    header_parts.append(ref)
        if title:  header_parts.append(f'"{title}"')
        if status: header_parts.append(f"({status})")
        header = " ".join(header_parts)

        parts.append(f"{header}\n{text}")
        raw_cits.append({
            "ref":    ref or f"#{i}",
            "title":  title,
            "type":   doc_type,
            "status": status,
            "score":  round(_json_safe_float(meta.get("rerank_score", 0.0)), 4),
        })
        total += len(text)

    return "\n\n---\n\n".join(parts), raw_cits


def _unique_by_source(docs: List[Document], limit: int, max_per_source: int = 3) -> List[Document]:
    """
    Keep top documents while allowing multiple chunks per source_id/ref.
    This prevents one document from dominating context while ensuring we get
    more than just the header/title page of a document.
    """
    out: List[Document] = []
    counts = {}  # {key: count}
    for doc in docs:
        meta = doc.metadata or {}
        key = meta.get("source_id") or meta.get("ref_number") or meta.get("title")
        if not key:
            key = id(doc)
            
        current_count = counts.get(key, 0)
        if current_count >= max_per_source:
            continue
            
        counts[key] = current_count + 1
        out.append(doc)
        
        if len(out) >= limit:
            break
    return out


def _parse_answer_citations_suggestions(raw: str) -> Tuple[str, List[dict], List[str], str, str]:
    """
    Parse the LLM output into:
      answer     : clean prose text from [ANSWER] block
      citations  : list of dicts extracted from [[REF|TITLE|TYPE|EXCERPT]] tags
      suggestions: list of strings from the ---SUGGESTIONS--- block
      reasoning  : text from [REASONING] block
      confidence : text from [CONFIDENCE] block
    """
    answer      = ""
    citations   = []
    suggestions = []
    reasoning   = ""
    confidence  = ""

    # 1. Extract ---SUGGESTIONS---
    sug_match = re.search(r'---SUGGESTIONS---\s*(\[.*?\])', raw, re.DOTALL | re.IGNORECASE)
    if sug_match:
        try:    suggestions = json.loads(sug_match.group(1))
        except: suggestions = []
        raw = raw[:sug_match.start()].strip()

    # 2. Extract Citations using Tag Format: [[ref|title|type|excerpt]]
    cit_marker = "---CITATIONS---"
    if cit_marker in raw:
        parts = raw.split(cit_marker)
        raw_content = parts[0].strip()
        cit_text = parts[1].strip()
        
        # Match [[ ... | ... | ... | ... ]]
        matches = re.findall(r'\[\[(.*?)\|(.*?)\|(.*?)\|(.*?)\]\]', cit_text)
        for ref, title, doc_type, excerpt in matches:
            citations.append({
                "ref":     ref.strip(),
                "title":   title.strip(),
                "type":    doc_type.strip(),
                "excerpt": excerpt.strip()
            })
    else:
        raw_content = raw.strip()

    # 3. Extract [REASONING], [ANSWER], [CONFIDENCE] blocks
    # Looking for blocks started by bracketed headers
    reason_match = re.search(r'\[REASONING\](.*?)(?=\[ANSWER\]|\[CONFIDENCE\]|$)', raw_content, re.DOTALL | re.IGNORECASE)
    if reason_match:
        reasoning = reason_match.group(1).strip()
    
    answer_match = re.search(r'\[ANSWER\](.*?)(?=\[CONFIDENCE\]|\[REASONING\]|$)', raw_content, re.DOTALL | re.IGNORECASE)
    if answer_match:
        answer = answer_match.group(1).strip()
    else:
        # Fallback if no specific block found, use everything but reasoning/confidence
        answer = raw_content

    conf_match = re.search(r'\[CONFIDENCE\](.*?)$', raw_content, re.DOTALL | re.IGNORECASE)
    if conf_match:
        confidence = conf_match.group(1).strip()

    # Clamp suggestions
    suggestions = [s for s in suggestions if isinstance(s, str)][:4]

    return answer, citations, suggestions, reasoning, confidence


from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import HumanMessagePromptTemplate, MessagesPlaceholder


def _classify_sop_inventory_query(query: str) -> Optional[Literal["count", "list"]]:
    """
    Detects SOP inventory questions so we can return a deterministic count/list
    without LLM drift. "count" = how many; "list" = enumerate SOPs.
    """
    q = (query or "").lower()
    if not re.search(
        r"\b(sop|sops|standard operating procedures?)\b",
        q,
        re.IGNORECASE,
    ):
        return None
    has_list_intent = bool(
        re.search(
            r"\b(list all|list every|show all|show me all|get all|name all|enumerate|all sops|every sop)\b",
            q,
        )
    ) or bool(re.search(r"\b(list|show)\b.+\b(sop|sops)\b", q)) or bool(
        re.search(r"\b(which|what) sops\b", q)
    )
    has_count_intent = any(
        p in q
        for p in (
            "how many",
            "how much",
            "number of",
            "total",
            "count ",
            " count",
            "quantity",
            "sop count",
        )
    )
    if re.search(r"\bkitne\b", q):
        has_count_intent = True
    if re.search(r"\b(how many sops|count sops|sop count|number of sops|total sops)\b", q):
        has_count_intent = True
    if re.search(
        r"\b(do we have|have we|is there|are there)\b", q
    ) and re.search(r"\b(sop|sops)\b", q):
        has_count_intent = True

    if has_list_intent and not has_count_intent:
        return "list"
    if has_count_intent and not has_list_intent:
        return "count"
    if has_list_intent and has_count_intent:
        if re.search(r"\bhow many\b", q) or re.search(
            r"\b(number|count|total) of\b", q
        ):
            return "count"
        return "list"
    if re.search(
        r"\b(available|exist|in the (system|index|database))\b", q
    ) and re.search(r"\bwhich\b.*\b(sop|sops)\b", q):
        return "list"
    if re.search(r"\b(available|exist|inventory)\b", q) and re.search(
        r"\b(how many|count|number)\b", q
    ):
        return "count"
    return None


def _strict_sop_inventory_response(
    docs: List[Document],
    query: str,
    retriever: HybridRetriever | None = None,
    mode: Literal["count", "list"] = "list",
) -> dict:
    """Build deterministic SOP inventory from the SOP section corpus (deduped by SOP id)."""
    inventory_docs: List[Document] = list(docs or [])
    if retriever is not None:
        try:
            corpus_docs, _ = retriever._get_bm25_corpus()
            if corpus_docs:
                inventory_docs = corpus_docs
        except Exception:
            pass

    rows: List[Tuple[str, str, str]] = []
    seen: set = set()
    for doc in inventory_docs:
        meta = doc.metadata or {}
        et = str(meta.get("entity_type", "")).lower()
        if rag_unified_enabled() and et and et != "sop":
            continue
        ref = (
            (meta.get("ref_number") or meta.get("sop_number") or meta.get("source_id"))
            or ""
        )
        if not ref and meta.get("entity_id"):
            ref = f"id:{str(meta.get('entity_id'))[:8]}"
        title = meta.get("title") or "Untitled SOP"
        status = meta.get("status") or "Unknown"
        page_content = (doc.page_content or "").strip()

        if (not ref or ref.startswith("id:")) and page_content:
            first_line = page_content.splitlines()[0].strip()
            if " - " in first_line:
                maybe_ref, maybe_title = first_line.split(" - ", 1)
                if maybe_ref.strip() and not maybe_ref.strip().lower().startswith(
                    "id:"
                ):
                    ref = maybe_ref.strip()
                if maybe_title.strip() and title == "Untitled SOP":
                    title = maybe_title.strip()

        eid = str(meta.get("entity_id") or "").lower()
        dedupe_key = f"{eid}|{(ref or '').lower()}" if eid else f"r|{(ref or title).lower()}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        display_ref = ref or title
        rows.append((display_ref, title, status))

    rows = sorted(rows, key=lambda x: (x[0] or "").lower())
    total = len(rows)
    list_cap = int(os.getenv("SOP_INVENTORY_LIST_MAX", "50"))

    if mode == "count":
        if total == 0:
            count_answer = (
                "Summary: No SOPs were found in the current search index. "
                "The index may be empty or SOPs may not be embedded yet.\n\n"
                "If you need a list, ask: “List all SOPs” after indexing has completed."
            )
        else:
            count_answer = (
                f"Summary: The search index currently contains {total} distinct SOP(s). "
                f"That number is a count of unique SOP record references (SOP id / number) "
                f"in the indexed SOP data, not the number of text chunks.\n\n"
                f"If you need the full list with titles, ask: “List all SOPs”."
            )
        return {
        "answer": count_answer,
        "citations": [
            {
                "ref": f"INDEX-SOP-COUNT({total})",
                "title": "Indexed SOP inventory",
                "type": "sop",
                "excerpt": f"Distinct SOPs in SOP index: {total}.",
            }
        ],
        "suggestions": [
            "List all SOPs with titles and status",
            "What does SOP-IT-001 cover?",
            "Which SOPs mention access control?",
        ],
        "retrieval_stats": {},
        "routed_to": "SOPs (strict count)",
        "cached": False,
        "metadata_snapshot": [],
        "audit_log_snapshot": [],
        "action_metadata": {
            "query": query,
            "routing": ["sops"],
            "latency_ms": 0.0,
            "timestamp": time.time(),
            "model": "deterministic",
            "strict_mode": "sop_inventory_count",
        },
    }

    key_points = "\n".join(
        [f"- {ref}: {title} [{status}]" for ref, title, status in rows[:list_cap]]
    )
    if total > list_cap:
        key_points += f"\n- … and {total - list_cap} more (truncated; increase SOP_INVENTORY_LIST_MAX to show more in list mode)."
    sources_lines = "\n".join(
        [f"- {ref}: {title} (SOP)" for ref, title, _ in rows[:list_cap]]
    )
    citations = [
        {"ref": ref, "title": title, "type": "SOP", "excerpt": f"Status: {status}"}
        for ref, title, status in rows[: list_cap * 2]
    ][:200]
    suggestions = [
        "How many SOPs are in the index?",
        "Show details for a specific SOP by number",
        "Find SOPs related to access control",
    ]

    answer = (
        f"Summary: There are {total} unique SOP record(s) in the indexed SOP data.\n\n"
        f"List:\n{key_points if key_points else 'No SOPs found in the current index.'}\n\n"
        f"Documents:\n{sources_lines if sources_lines else 'None.'}"
    )

    return {
        "answer": answer,
        "citations": citations,
        "suggestions": suggestions,
        "retrieval_stats": {},
        "routed_to": "SOPs",
        "cached": False,
        "metadata_snapshot": [],
        "audit_log_snapshot": [],
        "action_metadata": {
            "query": query,
            "routing": ["sops"],
            "latency_ms": 0.0,
            "timestamp": time.time(),
            "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "strict_mode": "sop_inventory",
        },
    }


class SmartRAGChain:
    """
    Intelligent RAG chain that:
      1. Routes the query to the relevant collection(s) only.
      2. Does Hybrid Search (Dense + BM25) + Cross-Encoder reranking.
      3. Injects chat history for multi-turn memory + CoT reasoning.
      4. Returns: clean prose answer | citations | dynamic suggestions.
    """

    def __init__(self, federated_retriever: FederatedRetriever):
        self.federated = federated_retriever
        self.llm = get_llm()
        self.router = LLMRouter(llm=self.llm)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=SMART_SYSTEM),
            MessagesPlaceholder(variable_name="chat_history_messages"),
            HumanMessagePromptTemplate.from_template(SMART_USER),
        ])


    def _extract_metadata_filters(self, query: str) -> dict:
        """
        Extracts department or specific document reference filters from the query.
        Example: 'IT/sops' -> {'department': 'IT'}
        Example: 'SOP-IT-001' -> {'ref_number': 'SOP-IT-001'}
        """
        filters = {}
        q = query.upper()
        
        # 1. Department pattern (e.g. IT/sops, HR documents)
        dept_match = re.search(r'\b(IT|HR|FINANCE|QUALITY|COMPLIANCE|SECURITY|OPS|LEGAL)\b', q)
        if dept_match:
            filters["department"] = dept_match.group(1)
            
        # 2. Document ID pattern (e.g. SOP-xxx, DEV-xxx)
        id_match = re.search(r'\b(SOP|DEV|CAPA|AUDIT|DEC)-[A-Z0-9-]+\b', q)
        if id_match:
            filters["ref_number"] = id_match.group(0)
            
        return filters

    def _find_active_doc_id(self, chat_history: List[Dict]) -> str:
        """Scan last 2-3 messages in history for any document IDs (SOP, DEV, etc)."""
        if not chat_history:
            return ""
        
        # Scan in reverse, looking for document ID patterns
        pattern = re.compile(r'\b(SOP|DEV|CAPA|AUDIT|DEC)-[A-Z0-9-]+\b', re.IGNORECASE)
        for msg in reversed(chat_history[-4:]):
            content = msg.get("content", "")
            match = pattern.search(content)
            if match:
                return match.group(0).upper()
        return ""

    def invoke(self, query: str, category: str = None, chat_history: List[Dict] = None) -> dict:
        t0 = time.time()

        cat_norm = (category or "").strip().lower()
        sop_inventory_mode: Optional[Literal["count", "list"]] = None
        if (not cat_norm) or cat_norm == "sops":
            sop_inventory_mode = _classify_sop_inventory_query(query)

        # ── Step 0: Extract Metadata Filters & Active Doc ID ──
        metadata_filters = self._extract_metadata_filters(query)
        active_doc_id = self._find_active_doc_id(chat_history) if chat_history else ""
        if active_doc_id and not sop_inventory_mode:
            print(f"  [context] identified active doc from history: {active_doc_id}")
            is_sop_query = any(
                k in (query or "").lower() for k in ["sop", "procedure", "standard"]
            )
            if active_doc_id.startswith("SOP") and is_sop_query:
                metadata_filters["ref_number"] = active_doc_id
        if sop_inventory_mode == "count" and not re.search(
            r"\bSOP-[A-Z0-9-]+\b", query or "", re.IGNORECASE
        ):
            metadata_filters.pop("ref_number", None)

        print(
            f"  [filters] extracted: {metadata_filters} | sop_inventory_mode: {sop_inventory_mode}"
        )

        # ── Step 1: Route query using LLM Router (Prompt 3) ──
        if category and category.strip().lower() in {
            "sops",
            "deviations",
            "capas",
            "audits",
            "decisions",
        }:
            target_sections = [category.strip().lower()]
            route_data = {"collections": target_sections, "exact_filters": dict(metadata_filters)}
        elif sop_inventory_mode:
            target_sections = ["sops"]
            route_data = {"collections": ["sops"], "exact_filters": dict(metadata_filters)}
        else:
            route_data = self.router.route(query)
            target_sections = route_data.get("collections", [])
            metadata_filters.update(route_data.get("exact_filters", {}))

        routed_label = describe_route(target_sections)
        print(f"  [router] '{query[:60]}' -> {target_sections} | filters: {metadata_filters}")
        # ── Step 2: Hybrid search on targeted collections only ──
        all_docs: List[Document] = []
        per_section_counts: Dict[str, int] = {}

        for section in target_sections:
            retriever = self.federated.retrievers.get(section)
            if not retriever:
                continue
            try:
                # Apply metadata filters (if any)
                retriever.metadata_filters = metadata_filters
                if rag_unified_enabled():
                    retriever.category_filter = section
                else:
                    retriever.category_filter = None
                # Deep retrieval: fetch 30 to allow for deduplication/diversification
                docs = retriever.invoke(query)
                
                # Rerank within this section
                top_n = 20 if len(target_sections) == 1 else 10
                ranked = self.federated.reranker.rerank_top_n(query, docs, top_n)
                
                # Deduplicate but allow more content depth (3-4 chunks per source)
                # If we have a single targeted document, we can afford more depth.
                max_chunks = 6 if active_doc_id else 4
                unique_limit = 15 if len(target_sections) == 1 else 8
                
                ranked = _unique_by_source(ranked, unique_limit, max_per_source=max_chunks)
                
                # Tag each doc with its section
                for d in ranked:
                    d.metadata["_section"] = section
                all_docs.extend(ranked)
                per_section_counts[section] = len(ranked)
            except Exception as e:
                print(f"  [router] Warning: retrieval failed for '{section}': {e}")
                per_section_counts[section] = 0

        if not all_docs:
            if sop_inventory_mode:
                strict_resp = _strict_sop_inventory_response(
                    [],
                    query,
                    self.federated.retrievers.get("sops"),
                    mode=sop_inventory_mode,
                )
                strict_resp["retrieval_stats"] = {
                    "searched": target_sections,
                    "per_section": per_section_counts,
                    "total_docs": 0,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                    "strict_mode": True,
                }
                return strict_resp
            return {
                "answer": "No relevant information found in the knowledge base for your query.",
                "citations": [],
                "suggestions": [
                    "Ask about a specific SOP number",
                    "Search for related deviations",
                    "Check CAPA status",
                ],
                "retrieval_stats": {
                    "searched": target_sections,
                    "total_docs": 0,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                },
                "routed_to": routed_label,
            }

        if sop_inventory_mode:
            strict_resp = _strict_sop_inventory_response(
                all_docs,
                query,
                self.federated.retrievers.get("sops"),
                mode=sop_inventory_mode,
            )
            strict_resp["retrieval_stats"] = {
                "searched": target_sections,
                "per_section": per_section_counts,
                "total_docs": len(all_docs),
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "strict_mode": True,
            }
            return strict_resp

        # ── Step 3: Build unified context ──
        context_str, raw_cits = _build_unified_context(all_docs, "document")

        # ── Step 3b: Format chat history for CoT continuity ──
        chat_history_messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role")
                content = msg.get("content", "").strip()
                if role == "assistant":
                    content = _truncate_text(content, MAX_HISTORY_MESSAGE_CHARS)
                    chat_history_messages.append(AIMessage(content=content))
                else:
                    content = _truncate_text(content, MAX_HISTORY_MESSAGE_CHARS)
                    chat_history_messages.append(HumanMessage(content=content))

            if len(chat_history_messages) > MAX_HISTORY_MESSAGES:
                chat_history_messages = chat_history_messages[-MAX_HISTORY_MESSAGES:]

        # ── Step 4: LLM generation ──
        query = _truncate_text(query, MAX_QUERY_CHARS)
        context_str = _truncate_text(context_str, MAX_CONTEXT_CHARS)
        try:
            history_focus = f"HISTORY FOCUS: Priority should be given to {active_doc_id} as it was discussed recently." if active_doc_id else ""
            raw_answer = (self.prompt | self.llm | StrOutputParser()).invoke({
                "context":      context_str,
                "question":     query,
                "chat_history_messages": chat_history_messages,
                "history_focus": history_focus,
            })
        except Exception as e:
            err = str(e).lower()
            if "503" in err or "unavailable" in err or "high demand" in err:
                fallback_llm = get_fallback_llm()
                raw_answer = (self.prompt | fallback_llm | StrOutputParser()).invoke({
                    "context":      context_str,
                    "question":     query,
                    "chat_history_messages": chat_history_messages,
                })
            else:
                raise

        # ── Step 5: Parse answer, citations, suggestions, reasoning, confidence ──
        answer, llm_citations, suggestions, reasoning, confidence = _parse_answer_citations_suggestions(raw_answer)

        # Merge LLM-parsed citations with raw retrieval metadata for richer response
        final_citations = []
        used_refs = set()
        for lc in llm_citations:
            ref = lc.get("ref", "")
            # Try to enrich from raw_cits
            match = next((r for r in raw_cits if ref in r.get("ref", "") or (r.get("title") and r["title"] in lc.get("title", ""))), None)
            entry = {
                "ref":     ref,
                "title":   lc.get("title", match.get("title","") if match else ""),
                "type":    lc.get("type", match.get("type","") if match else ""),
                "excerpt": lc.get("excerpt", ""),
                "status":  match.get("status","") if match else "",
                "score":   _json_safe_float(
                    (match.get("score", 0.0) if match else 0.0)
                ),
            }
            if ref not in used_refs:
                final_citations.append(entry)
                used_refs.add(ref)

        # Fall back to raw citations if LLM did not produce any
        if not final_citations:
            final_citations = raw_cits
        final_citations = _sanitize_citation_list(final_citations)

        # ── Step 6: Assemble full Audit Vault snapshots ──

        metadata_snapshot = []
        audit_log_snapshot = []
        
        seen_docs = set()
        for doc in all_docs:
            source_id = doc.metadata.get("source_id")
            if source_id not in seen_docs:
                metadata_snapshot.append(doc.metadata.get("full_metadata", doc.metadata))
                audit_log_snapshot.extend(doc.metadata.get("audit_trail", []))
                seen_docs.add(source_id)

        latency_ms = round((time.time() - t0) * 1000, 1)

        return {
            "answer":      answer,
            "reasoning":   reasoning,
            "confidence":  confidence,
            "citations":   final_citations,
            "suggestions": suggestions,
            "retrieval_stats": {
                "searched":     target_sections,
                "per_section":  per_section_counts,
                "total_docs":   len(all_docs),
                "latency_ms":   latency_ms,
            },
            "routed_to":   routed_label,
            "cached":      False,
            # Audit Vault Fields
            "metadata_snapshot":  metadata_snapshot,
            "audit_log_snapshot": audit_log_snapshot,
            "action_metadata": {
                "query": query,
                "routing": target_sections,
                "latency_ms": latency_ms,
                "timestamp": time.time(),
                "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            }
        }


# Keep FederatedRAGChain as alias for backward compat
FederatedRAGChain = SmartRAGChain
