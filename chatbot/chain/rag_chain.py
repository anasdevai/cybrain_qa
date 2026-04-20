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
from typing import Dict, List, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import CrossEncoderReranker
from retrieval.context_builder import build_context
from retrieval.federated_retriever import FederatedRetriever
from retrieval.query_router import route_query, describe_route
from retrieval.llm_router import LLMRouter
import os


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
production Hybrid RAG system.

You have access to a structured Qdrant vector database with the following SEPARATE
collections. You MUST search the correct collection based on the user's intent:

═══════════════════════════════════════════════════════════════
COLLECTION MAP
═══════════════════════════════════════════════════════════════

Collection: "sops"
  → Contains : Standard Operating Procedures (SOPs)
  → Fields   : sop_number, title, department, sop_content,
                version_number, effective_date, review_date, status
  → Trigger keywords: "SOP", "procedure", "standard", "policy",
    "how to", "zugriffsmanagement", "patch", "firewall", "notfall",
    "KI-Systeme", "governance"

Collection: "deviations"
  → Contains : Deviation records and incidents
  → Fields   : deviation_number, title, description_text,
                root_cause_text, impact_level, external_status, event_date
  → Trigger keywords: "deviation", "incident", "issue", "problem",
    "DEV-", "breach", "excursion", "fehler", "abweichung", "kritisch"

Collection: "sop_versions"
  → Contains : Specific version content of SOPs
  → Fields   : version_number, content_json, effective_date,
                review_date, external_version_id, external_status
  → Trigger keywords: "version", "current version", "v4", "effective",
    "latest revision", "content of", "what does SOP say"

Collection: "capas"
  → Contains : Corrective and Preventive Actions
Collection: "audits"
  → Contains : Audit findings
Collection: "decisions"
  → Contains : Justifications and resolution

═══════════════════════════════════════════════════════════════
RULES YOU MUST ALWAYS FOLLOW
═══════════════════════════════════════════════════════════════

RULE 1 — COLLECTION ROUTING
Before answering, explicitly identify which collection(s) to search.
Never merge data from deviations into SOPs or vice versa unless the user
explicitly asks for a cross-reference.

RULE 2 — EXACT POINT MATCHING
When the user mentions a specific identifier (e.g., "SOP-IT-001",
"DEV-IT-401"), you MUST filter on that exact field value.
Do not rely on semantic similarity alone.

RULE 3 — CHAIN OF THOUGHT
Before generating your final answer, you MUST perform and show a brief
reasoning block tagged as [REASONING]. In this block:
  (a) identify what the user is asking
  (b) decide which collection to search
  (c) identify any exact identifiers to filter on
  (d) plan your answer structure
Then produce your [ANSWER].

RULE 4 — CITATIONS
Every factual claim in your answer MUST be linked to its source record
using this format: [SOP-IT-001], [DEV-IT-401], [SOP-QA-010 v4.0]
Never state a fact without a citation tag.
If you cannot cite it, do not state it.

RULE 5 — CONVERSATION MEMORY
You have access to the full conversation history. When the user says
"that deviation", "the one we just discussed", "same SOP", "previous answer"
— you MUST resolve the reference from earlier in the conversation history.
Never ask the user to repeat what they already told you.

RULE 6 — IMPACT LEVEL AWARENESS
When discussing deviations, always surface the impact_level in your answer.
Priority order: Critical > Major > Moderate > Minor
Flag Critical and Major deviations explicitly with a ⚠️ marker.

RULE 7 — BILINGUAL HANDLING
This system contains both German and English documents.
If the user asks in English about a German SOP title, translate the intent
correctly and search both languages.
Return the answer in the same language the user asked in.

RULE 8 — STATUS AWARENESS
Always report the current status of records:
  - Deviations  : open | under_investigation | closed
  - SOP versions: effective | draft | obsolete
Never present a closed deviation or obsolete SOP version as currently active.

RULE 9 — CROSS-REFERENCE DETECTION
If the user asks about a deviation, check if a related SOP exists that
governs that area.
Example: DEV-IT-101 → SOP-IT-001 (OT access management)
Proactively surface this link as: [RELATED SOP: SOP-IT-001]

RULE 10 — REFUSAL RULE
If the retrieved context does not contain enough information to answer
confidently, say:
"The available records do not contain sufficient detail to answer this
question. Please check [collection name] or provide more context."
Never hallucinate fields, dates, or root causes that are null or missing
in the data.
"""

SMART_USER = """\
## {history_focus}

CONVERSATION HISTORY:
(Loaded implicitly via message sequence)

─────────────────────────────────────────
RETRIEVED CONTEXT:
{context}

─────────────────────────────────────────
USER QUESTION:
{question}

─────────────────────────────────────────
INSTRUCTIONS FOR THIS RESPONSE:

STEP 1 — [REASONING]
Answer each sub-question before writing your final answer:
  • What is the user asking? (one sentence)
  • Which collection did I search? Why?
  • Did I apply any exact identifier filter? Which field and value?
  • Did the user reference something from earlier in the conversation?
    If yes, what exactly?
  • What is the impact_level / status of the records involved?
  • Are there any cross-collection links I should surface?

STEP 2 — [ANSWER]
  • Answer the question directly and completely.
  • Cite every fact using bracket notation:
    [SOP-IT-001], [DEV-IT-401], [DEV-2026-103]
  • For deviations with impact_level Critical or Major, prepend ⚠️
  • If a related SOP governs the deviation topic, add at the end:
    [RELATED SOP: SOP-XX-XXX — title]
  • If the question was about a specific version, include version number
    and effective date in your citation:
    [SOP-QA-010 v4.0 | effective: 2026-01-01]

  Use this structure for complex answers:
  ┌─ Summary    : one paragraph direct answer
  ├─ Details    : bullet points with citations per fact
  ├─ Status     : current status of the record(s)
  └─ Cross-refs : related SOPs or deviations (if applicable)

STEP 3 — [CONFIDENCE]
  State your confidence level for this answer:
  • HIGH   — exact record found via identifier filter
  • MEDIUM — semantic match found, recommend manual verification
  • LOW    — insufficient data; refusal rule applies

─────────────────────────────────────────
FORMAT RULES:
  ✗ Never use vague language like "the document mentions..."
    → Always name the exact record: [SOP-IT-001], [DEV-IT-401]
  ✗ Never present null fields (root_cause_text: null) as if they have content
  ✗ Never exceed 400 words unless the user explicitly asks for full detail
  ✓ Always end with: 📎 Sources: [list every cited record ID]

## REQUIRED SYSTEM PARSING BLOCKS (YOU MUST INCLUDE THESE AFTER YOUR ANSWER)

---CITATIONS---
[[REF_ID|Document Title|Type|One sentence excerpt]]
[[REF_ID|Document Title|Type|One sentence excerpt]]
(Put each citation on a NEW line starting with [[ and ending with ]]. Use '|' as separator. This section is for metadata only and will be parsed out.)

---SUGGESTIONS---
["Follow-up question 1 using doc IDs", "Follow-up question 2", "Follow-up question 3"]
"""


def _build_unified_context(docs: List[Document], prefix_label: str) -> Tuple[str, List[dict]]:
    """Build a numbered context string from retrieved docs, regardless of collection."""
    if not docs:
        return "", []

    parts, raw_cits = [], []
    total = 0
    MAX = 14000

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
            "score":  round(float(meta.get("rerank_score", 0.0)), 4),
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


def _is_sop_count_or_list_query(query: str, target_sections: List[str]) -> bool:
    """Detect strict SOP inventory intent to avoid LLM hallucinated counts."""
    q = query.lower().strip()
    if target_sections != ["sops"]:
        return False
    has_sop = "sop" in q
    asks_count = any(k in q for k in ["how many", "count", "number of", "total", "kitne"])
    asks_list = any(k in q for k in ["list", "show all", "all sops", "which sops", "what sops", "have"])
    return has_sop and (asks_count or asks_list)


def _strict_sop_inventory_response(docs: List[Document], query: str) -> dict:
    """Build deterministic SOP inventory response from retrieved docs only."""
    rows = []
    seen = set()
    for doc in docs:
        meta = doc.metadata or {}
        ref = meta.get("ref_number") or meta.get("source_id") or ""
        title = meta.get("title") or "Untitled SOP"
        status = meta.get("status") or "Unknown"
        if not ref or ref in seen:
            continue
        seen.add(ref)
        rows.append((ref, title, status))

    rows = sorted(rows, key=lambda x: x[0])
    total = len(rows)
    key_points = "\n".join([f"- {ref}: {title} [{status}]" for ref, title, status in rows[:20]])
    sources_table = "\n".join(
        [f"| {ref} | {title} | SOP | Inventory match |" for ref, title, _ in rows]
    )
    citations = [{"ref": ref, "title": title, "type": "SOP", "excerpt": f"Status: {status}"} for ref, title, status in rows]
    suggestions = [
        "Show details for SOP-IT-001",
        "Compare SOP statuses across all SOPs",
        "Find SOPs related to access control",
    ]

    answer = (
        "### Direct Answer\n"
        f"There are {total} SOPs in the indexed SOP dataset.\n\n"
        "### Key Points\n"
        f"{key_points if key_points else '- No SOPs found in the current index.'}\n\n"
        "### Summary\n"
        f"The SOP inventory currently contains {total} unique SOP records.\n\n"
        "### Sources\n"
        "| Document ID | Title | Type | Relevance |\n"
        "|-------------|-------|------|-----------|\n"
        f"{sources_table if sources_table else '| - | - | SOP | No records found |'}"
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
        
        # ── Step 0: Extract Metadata Filters & Active Doc ID ──
        metadata_filters = self._extract_metadata_filters(query)
        active_doc_id = self._find_active_doc_id(chat_history) if chat_history else ""
        if active_doc_id:
            print(f"  [context] identified active doc from history: {active_doc_id}")
            # If active_doc_id found, ensure it's in the filters if the query targets that type
            is_sop_query = any(k in query.lower() for k in ["sop", "procedure", "standard"])
            if active_doc_id.startswith("SOP") and is_sop_query:
                metadata_filters["ref_number"] = active_doc_id

        print(f"  [filters] extracted: {metadata_filters}")

        # ── Step 1: Route query using LLM Router (Prompt 3) ──
        if category and category.strip().lower() in {"sops", "deviations", "capas", "audits", "decisions"}:
            target_sections = [category.strip().lower()]
            route_data = {"collections": target_sections, "exact_filters": metadata_filters}
        else:
            route_data = self.router.route(query)
            target_sections = route_data.get("collections", [])
            # Merge router filters with manually extracted ones
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
            return {
                "answer":          "No relevant information found in the knowledge base for your query.",
                "citations":       [],
                "suggestions":     ["Ask about a specific SOP number", "Search for related deviations", "Check CAPA status"],
                "retrieval_stats": {"searched": target_sections, "total_docs": 0, "latency_ms": round((time.time()-t0)*1000, 1)},
                "routed_to":       routed_label,
            }

        # ── Strict deterministic path for SOP inventory queries ──
        if _is_sop_count_or_list_query(query, target_sections):
            strict_resp = _strict_sop_inventory_response(all_docs, query)
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
                    if len(content) > 800:
                        content = content[:800] + "…"
                    chat_history_messages.append(AIMessage(content=content))
                else:
                    chat_history_messages.append(HumanMessage(content=content))

        # ── Step 4: LLM generation ──
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
                "score":   match.get("score", 0.0) if match else 0.0,
            }
            if ref not in used_refs:
                final_citations.append(entry)
                used_refs.add(ref)

        # Fall back to raw citations if LLM did not produce any
        if not final_citations:
            final_citations = raw_cits

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
