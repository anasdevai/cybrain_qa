from html import escape
import re
import os
import threading
import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import or_
from langchain_core.output_parsers import StrOutputParser

from action.prompts import build_gap_check_prompt, build_improve_prompt, build_rewrite_prompt
from action.runtime import create_action_runtime
from action.utils import format_chunks, parse_with_retry
from schemas.sop_actions import ActionRequest, GapCheckResponse, ImproveResponse, RewriteResponse
from .schemas import AIActionRequest, AIActionResponse
from .database import SessionLocal
from .models import SOP, SOPVersion, Deviation, Capa, AuditFinding, Decision

# RAG-specific imports are lazy-loaded inside _get_smart_rag_chain()
# to avoid ModuleNotFoundError when running without the RAG chatbot modules.
# Modules: embeddings.embedder, retrieval.*, chain.rag_chain, langchain_qdrant, qdrant_client

ai_router = APIRouter()
_smart_rag_lock = threading.Lock()
_smart_rag_chain = None
_action_runtime_lock = threading.Lock()
_action_runtime = None
CHAT_QUERY_TIMEOUT_SECONDS = int(os.getenv("CHAT_QUERY_TIMEOUT_SECONDS", "25"))
SOP_REF_PATTERN = re.compile(r"\bSOP-[A-Z0-9-]+\b", re.IGNORECASE)
DEV_REF_PATTERN = re.compile(r"\bDEV-[A-Z0-9-]+\b", re.IGNORECASE)
CAPA_REF_PATTERN = re.compile(r"\bCAPA-[A-Z0-9-]+\b", re.IGNORECASE)
AUDIT_REF_PATTERN = re.compile(r"\bAUDIT-[A-Z0-9-]+\b", re.IGNORECASE)
DECISION_REF_PATTERN = re.compile(r"\bDEC-[A-Z0-9-]+\b", re.IGNORECASE)
CHATBOT_USE_LOCAL_DB = os.getenv("CHATBOT_USE_LOCAL_DB", "true").strip().lower() == "true"


from typing import Any

def _get_smart_rag_chain() -> Any:
    """
    Lazy-load chatbot runtime so the main backend starts even if
    optional RAG env vars are missing.
    """
    global _smart_rag_chain
    if _smart_rag_chain is not None:
        return _smart_rag_chain

    with _smart_rag_lock:
        if _smart_rag_chain is not None:
            return _smart_rag_chain

        from qdrant_client import QdrantClient
        from langchain_qdrant import QdrantVectorStore
        from embeddings.embedder import get_embedder
        from retrieval.federated_retriever import FederatedRetriever
        from retrieval.reranker import CrossEncoderReranker
        from chain.rag_chain import SmartRAGChain

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        if not qdrant_url:
            raise RuntimeError("QDRANT_URL is not configured")

        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        embedder = get_embedder()
        reranker = CrossEncoderReranker(top_n=5)

        collection_map = {
            "sops": os.getenv("COLLECTION_SOPS", "docs_sops"),
            "deviations": os.getenv("COLLECTION_DEVIATIONS", "docs_deviations"),
            "capas": os.getenv("COLLECTION_CAPAS", "docs_capas"),
            "audits": os.getenv("COLLECTION_AUDITS", "docs_audits"),
            "decisions": os.getenv("COLLECTION_DECISIONS", "docs_decisions"),
        }
        vectorstores = {
            section: QdrantVectorStore(client=client, collection_name=collection_name, embedding=embedder)
            for section, collection_name in collection_map.items()
        }
        federated = FederatedRetriever(client=client, vectorstores=vectorstores, reranker=reranker)
        for section, collection_name in collection_map.items():
            federated.retrievers[section].collection_name = collection_name

        _smart_rag_chain = SmartRAGChain(federated)
        return _smart_rag_chain


def _normalize_action(action: str) -> str:
    normalized = (action or "").strip().lower().replace("-", "_")
    aliases = {
        "gapcheck": "gap_check",
        "quality_check": "gap_check",
        "support": "improve",
    }
    return aliases.get(normalized, normalized)


def _get_action_runtime() -> Any:
    global _action_runtime
    if _action_runtime is not None:
        return _action_runtime

    with _action_runtime_lock:
        if _action_runtime is not None:
            return _action_runtime
        _action_runtime = create_action_runtime()
        return _action_runtime


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _split_sentences(text: str) -> list[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _extract_text_from_tiptap(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type")
    if node_type == "text":
        return str(node.get("text", ""))
    chunks: list[str] = []
    for child in node.get("content", []) or []:
        child_text = _extract_text_from_tiptap(child)
        if child_text:
            chunks.append(child_text)
    joiner = "\n" if node_type in {"paragraph", "heading", "listItem"} else " "
    return joiner.join(chunks).strip()


def _extract_sop_refs(question: str, chat_history: list[dict]) -> list[str]:
    refs = set(match.upper() for match in SOP_REF_PATTERN.findall(question or ""))
    for message in (chat_history or [])[-6:]:
        content = str(message.get("content", ""))
        for match in SOP_REF_PATTERN.findall(content):
            refs.add(match.upper())
    return sorted(refs)


def _extract_entity_refs(pattern: re.Pattern, question: str, chat_history: list[dict]) -> list[str]:
    refs = set(match.upper() for match in pattern.findall(question or ""))
    q_lower = (question or "").lower()
    list_intent = any(term in q_lower for term in [
        "all", "list", "show", "available", "which sops", "what sops", "sops",
        "which deviations", "what deviations", "deviations",
    ])
    follow_up_intent = any(term in q_lower for term in [
        "that", "same", "previous", "earlier", "this one", "the one",
        "wohi", "same sop", "same deviation",
    ])

    # Only pull refs from history for true follow-up questions.
    include_history = follow_up_intent and not list_intent
    if include_history:
        for message in (chat_history or [])[-6:]:
            content = str(message.get("content", ""))
            for match in pattern.findall(content):
                refs.add(match.upper())
    return sorted(refs)


def _build_local_db_chat_response(question: str, chat_history: list[dict], category: str | None) -> dict:
    q = (question or "").strip()
    q_like = f"%{q}%"
    q_lower = q.lower()
    q_tokens = [token for token in re.findall(r"[a-z0-9]+", q_lower) if len(token) >= 3]
    category = (category or "").strip().lower()
    db = SessionLocal()
    try:
        citations = []
        sources = []
        answer_parts = []

        def push_source(ref: str, title: str, source_type: str, excerpt: str):
            citations.append({
                "ref": ref,
                "title": title,
                "type": source_type,
                "status": "",
                "score": 1.0,
                "excerpt": excerpt,
            })
            sources.append({
                "id": ref,
                "type": source_type,
                "label": title or ref,
            })

        def _tokenized_clause(columns):
            if not q_tokens:
                return None
            clauses = []
            for token in q_tokens[:8]:
                token_like = f"%{token}%"
                for col in columns:
                    clauses.append(col.ilike(token_like))
            return or_(*clauses) if clauses else None

        wants_sops = category in {"", "sops", "sop", "all"} and (
            category in {"sops", "sop"} or "sop" in q_lower or "procedure" in q_lower or "policy" in q_lower
        )
        wants_deviations = category in {"", "deviations", "deviation", "all"} and (
            category in {"deviations", "deviation"} or "deviation" in q_lower or "deviations" in q_lower or "excursion" in q_lower
        )
        wants_capas = category in {"", "capas", "capa", "all"} and (
            category in {"capas", "capa"} or "capa" in q_lower or "corrective" in q_lower
        )
        wants_audits = category in {"", "audits", "audit", "all"} and (
            category in {"audits", "audit"} or "audit" in q_lower or "finding" in q_lower
        )
        wants_decisions = category in {"", "decisions", "decision", "all"} and (
            category in {"decisions", "decision"} or "decision" in q_lower
        )

        if not any([wants_sops, wants_deviations, wants_capas, wants_audits, wants_decisions]):
            # Broad natural-language query without explicit type: search SOP + deviations first.
            wants_sops = True
            wants_deviations = True

        # SOPs
        if wants_sops:
            sop_refs = _extract_entity_refs(SOP_REF_PATTERN, question, chat_history)
            sops = []
            if sop_refs:
                for ref in sop_refs[:5]:
                    row = db.query(SOP).filter(SOP.sop_number.ilike(ref)).first()
                    if row:
                        sops.append(row)
            else:
                token_clause = _tokenized_clause([SOP.sop_number, SOP.title, SOP.department])
                base = db.query(SOP)
                if token_clause is not None:
                    sops = base.filter(token_clause).limit(5).all()
                else:
                    sops = base.filter(
                        (SOP.sop_number.ilike(q_like)) |
                        (SOP.title.ilike(q_like)) |
                        (SOP.department.ilike(q_like))
                    ).limit(5).all()
                if not sops:
                    sops = base.order_by(SOP.updated_at.desc()).limit(5).all()

            for sop in sops:
                push_source(
                    sop.sop_number,
                    sop.title,
                    "sop",
                    f"SOP in department {sop.department or 'unknown'}."
                )
            if sops:
                answer_parts.append(
                    "SOP matches: " + ", ".join(f"{s.sop_number} ({s.title})" for s in sops)
                )

        # Deviations
        if wants_deviations:
            dev_refs = _extract_entity_refs(DEV_REF_PATTERN, question, chat_history)
            devs = []
            if dev_refs:
                for ref in dev_refs[:5]:
                    row = db.query(Deviation).filter(Deviation.deviation_number.ilike(ref)).first()
                    if row:
                        devs.append(row)
            else:
                token_clause = _tokenized_clause([Deviation.deviation_number, Deviation.title, Deviation.description_text])
                base = db.query(Deviation)
                if token_clause is not None:
                    devs = base.filter(token_clause).limit(5).all()
                else:
                    devs = base.filter(
                        (Deviation.deviation_number.ilike(q_like)) |
                        (Deviation.title.ilike(q_like)) |
                        (Deviation.description_text.ilike(q_like))
                    ).limit(5).all()
                if not devs:
                    devs = base.order_by(Deviation.updated_at.desc()).limit(5).all()
            for dev in devs:
                push_source(
                    dev.deviation_number,
                    dev.title,
                    "deviation",
                    f"Deviation status {dev.external_status or 'unknown'}, impact {dev.impact_level or 'unknown'}."
                )
            if devs:
                answer_parts.append(
                    "Deviation matches: " + ", ".join(f"{d.deviation_number} ({d.title})" for d in devs)
                )

        # CAPAs
        if wants_capas:
            capa_refs = _extract_entity_refs(CAPA_REF_PATTERN, question, chat_history)
            capas = []
            if capa_refs:
                for ref in capa_refs[:5]:
                    row = db.query(Capa).filter(Capa.capa_number.ilike(ref)).first()
                    if row:
                        capas.append(row)
            else:
                token_clause = _tokenized_clause([Capa.capa_number, Capa.title, Capa.action_text])
                base = db.query(Capa)
                if token_clause is not None:
                    capas = base.filter(token_clause).limit(5).all()
                else:
                    capas = base.filter(
                        (Capa.capa_number.ilike(q_like)) |
                        (Capa.title.ilike(q_like)) |
                        (Capa.action_text.ilike(q_like))
                    ).limit(5).all()
                if not capas:
                    capas = base.order_by(Capa.updated_at.desc()).limit(5).all()
            for capa in capas:
                push_source(
                    capa.capa_number,
                    capa.title,
                    "capa",
                    f"CAPA status {capa.external_status or 'unknown'}."
                )
            if capas:
                answer_parts.append(
                    "CAPA matches: " + ", ".join(f"{c.capa_number} ({c.title})" for c in capas)
                )

        # Audits
        if wants_audits:
            audit_refs = _extract_entity_refs(AUDIT_REF_PATTERN, question, chat_history)
            audits = []
            if audit_refs:
                for ref in audit_refs[:5]:
                    row = db.query(AuditFinding).filter(
                        (AuditFinding.audit_number.ilike(ref)) |
                        (AuditFinding.finding_number.ilike(ref))
                    ).first()
                    if row:
                        audits.append(row)
            else:
                token_clause = _tokenized_clause([AuditFinding.audit_number, AuditFinding.finding_number, AuditFinding.finding_text])
                base = db.query(AuditFinding)
                if token_clause is not None:
                    audits = base.filter(token_clause).limit(5).all()
                else:
                    audits = base.filter(
                        (AuditFinding.audit_number.ilike(q_like)) |
                        (AuditFinding.finding_number.ilike(q_like)) |
                        (AuditFinding.finding_text.ilike(q_like))
                    ).limit(5).all()
                if not audits:
                    audits = base.order_by(AuditFinding.updated_at.desc()).limit(5).all()
            for audit in audits:
                ref = audit.finding_number or audit.audit_number or "AUDIT"
                push_source(ref, ref, "audit", f"Audit finding status {audit.acceptance_status or 'unknown'}.")
            if audits:
                answer_parts.append(
                    "Audit matches: " + ", ".join((a.finding_number or a.audit_number or "AUDIT") for a in audits)
                )

        # Decisions
        if wants_decisions:
            dec_refs = _extract_entity_refs(DECISION_REF_PATTERN, question, chat_history)
            decisions = []
            if dec_refs:
                for ref in dec_refs[:5]:
                    row = db.query(Decision).filter(Decision.decision_number.ilike(ref)).first()
                    if row:
                        decisions.append(row)
            else:
                token_clause = _tokenized_clause([Decision.decision_number, Decision.title, Decision.decision_statement])
                base = db.query(Decision)
                if token_clause is not None:
                    decisions = base.filter(token_clause).limit(5).all()
                else:
                    decisions = base.filter(
                        (Decision.decision_number.ilike(q_like)) |
                        (Decision.title.ilike(q_like)) |
                        (Decision.decision_statement.ilike(q_like))
                    ).limit(5).all()
                if not decisions:
                    decisions = base.order_by(Decision.updated_at.desc()).limit(5).all()
            for dec in decisions:
                ref = dec.decision_number or dec.title or "DECISION"
                push_source(ref, dec.title, "decision", "Decision record matched in local database.")
            if decisions:
                answer_parts.append(
                    "Decision matches: " + ", ".join((d.decision_number or d.title or "Decision") for d in decisions)
                )

        if not citations:
            return {
                "answer": "No relevant local database records were found for this query.",
                "sources": [],
                "citations": [],
                "suggestions": [
                    "Ask with an exact SOP/DEV/CAPA number",
                    "Try a shorter and more specific query",
                    "Use category-specific wording (SOP, deviation, CAPA, audit, decision)",
                ],
                "retrieval_stats": {"mode": "local-db", "hits": 0},
                "routed_to": "local-db",
            }

        return {
            "answer": " ".join(answer_parts),
            "sources": sources,
            "citations": citations,
            "suggestions": [
                "Ask for details of one returned record",
                "Ask for status and ownership of a returned item",
                "Ask for related SOP/deviation/CAPA links",
            ],
            "retrieval_stats": {"mode": "local-db", "hits": len(citations)},
            "routed_to": "local-db",
        }
    finally:
        db.close()


def _build_sop_db_fallback(question: str, chat_history: list[dict]) -> dict | None:
    sop_refs = _extract_sop_refs(question, chat_history)
    if not sop_refs:
        return None

    db = SessionLocal()
    try:
        hits = []
        for sop_ref in sop_refs[:3]:
            sop = db.query(SOP).filter(SOP.sop_number.ilike(sop_ref)).first()
            if not sop:
                continue

            version = None
            if sop.current_version_id:
                version = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
            if not version:
                version = (
                    db.query(SOPVersion)
                    .filter(SOPVersion.sop_id == sop.id)
                    .order_by(SOPVersion.created_at.desc())
                    .first()
                )

            content_text = _clean_text(_extract_text_from_tiptap((version.content_json if version else {}) or {}))
            excerpt = content_text[:500]
            if len(content_text) > 500:
                excerpt += "..."

            hits.append({
                "sop_number": sop.sop_number,
                "title": sop.title,
                "status": (version.external_status if version else "") or "unknown",
                "version_number": (version.version_number if version else "") or "",
                "excerpt": excerpt or "No SOP body text available.",
            })

        if not hits:
            return None

        if len(hits) == 1:
            item = hits[0]
            answer = (
                f"{item['sop_number']} ({item['title']}) was found in the main SOP database. "
                f"Current status: {item['status']}."
            )
        else:
            refs = ", ".join(f"{item['sop_number']} ({item['title']})" for item in hits)
            answer = f"Found these SOP records in the main SOP database: {refs}."

        details = " ".join(
            f"{item['sop_number']}: {item['excerpt']}" for item in hits
        ).strip()
        if details:
            answer = f"{answer}\n\n{details}"

        citations = [
            {
                "ref": item["sop_number"],
                "title": item["title"],
                "type": "sop",
                "status": item["status"],
                "score": 1.0,
            }
            for item in hits
        ]

        sources = [
            {
                "id": item["sop_number"],
                "type": "sop",
                "label": item["title"] or item["sop_number"],
            }
            for item in hits
        ]

        return {
            "answer": answer,
            "sources": sources,
            "citations": citations,
            "suggestions": [
                f"Summarize {hits[0]['sop_number']} responsibilities",
                f"Show procedure steps from {hits[0]['sop_number']}",
                "Ask for related deviations or CAPAs",
            ],
            "retrieval_stats": {"fallback": "postgres_sop_lookup", "hits": len(hits)},
            "routed_to": "db-fallback-sops",
        }
    finally:
        db.close()


def _build_context(payload: AIActionRequest) -> str:
    bits = []
    if payload.sop_title:
        bits.append(f"SOP title: {payload.sop_title}")
    if payload.section_name:
        bits.append(f"Section name: {payload.section_name}")
    if payload.section_type:
        bits.append(f"Section type: {payload.section_type}")
    return " | ".join(bits) if bits else "SOP context unavailable"


def _paragraph(text: str) -> str:
    return f"<p>{escape(text)}</p>"


def _build_prompt(action: str, payload: AIActionRequest) -> str:
    context = _build_context(payload)
    if action == "gap_check":
        return (
            "You are a Lead GMP/QA Compliance Auditor with expertise in ISO 9001:2015, ISO 13485:2016, "
            "FDA 21 CFR Parts 11 and 820, and EU GMP Annex 11.\n\n"
            f"DOCUMENT CONTEXT: {context}\n\n"
            "YOUR TASK: Perform a thorough compliance gap analysis on the SOP text below. "
            "Check for: (1) missing or incomplete procedure steps, (2) undefined responsibilities \u2014 "
            "roles must be named specifically, (3) undefined frequencies or timelines \u2014 no vague terms like "
            "'regularly' or 'as needed', (4) missing data integrity or access controls, (5) absent "
            "documentation requirements including record names and retention periods, (6) ambiguous language "
            "and undefined technical terms, (7) missing regulatory references where required.\n\n"
            f"TEXT TO ANALYZE:\n{payload.text}\n\n"
            "Return ONLY a valid JSON object structured as: "
            '{"gaps": [{"issue": "short label", "explanation": "why this fails GMP/regulatory requirements", '
            '"recommendation": "exact SOP-ready text to fix the gap"}], '
            '"section_assessed": "section name"}'
        )
    if action == "rewrite":
        return (
            "You are a senior GMP/QA technical writer with expertise in ISO 13485, FDA 21 CFR, and EU GMP Annex 11.\n\n"
            f"DOCUMENT CONTEXT: {context}\n\n"
            "YOUR TASK: Perform a complete, professional rewrite of the SOP text below. Apply these standards: "
            "(1) Use active voice and imperative verbs throughout. (2) Every sentence must name a specific role "
            "as the subject \u2014 never 'someone' or 'the team'. (3) Replace all vague qualifiers with specific "
            "values, frequencies, or defined conditions. (4) Ensure logical, chronological process order. "
            "(5) Use parallel structure in lists. (6) Add critical step callouts where safety or compliance is at risk.\n"
            "RULES: Do NOT add Purpose/Scope/Responsibilities/Procedure headings. Do NOT change the core topic. "
            "You MAY restructure sentences and reorder information for flow.\n\n"
            f"TEXT TO REWRITE:\n{payload.text}\n\n"
            "Return ONLY a valid JSON object: "
            '{"rewritten_text": "full rewritten text", '
            '"structural_changes": ["change 1", "change 2"], '
            '"rationale": "2-sentence explanation of compliance and clarity improvements"}'
        )
    if action == "improve":
        return (
            "You are a senior GMP/QA technical writer specializing in regulatory SOP documentation.\n\n"
            f"DOCUMENT CONTEXT: {context}\n\n"
            "YOUR TASK: Make targeted, high-quality improvements to the SOP text below. Apply these criteria: "
            "(1) Fix all grammar, punctuation, and spelling errors. (2) Replace passive voice with active voice. "
            "(3) Replace vague qualifiers ('appropriate', 'as needed') with specific, measurable language. "
            "(4) Ensure responsibilities are attributed to named roles. (5) Make language imperative and unambiguous.\n"
            "STRICT RULES: Do NOT add SOP headings or restructure into a full SOP. Do NOT change factual content or meaning. "
            "Make only the smallest meaningful improvements required.\n\n"
            f"TEXT TO IMPROVE:\n{payload.text}\n\n"
            "Return ONLY a valid JSON object: "
            '{"improved_text": "the improved text", '
            '"changes_made": ["specific change 1", "specific change 2"], '
            '"compliance_note": "one sentence explaining the GMP/quality improvement achieved"}'
        )
    raise HTTPException(status_code=400, detail=f"Action '{action}' is not supported.")


def _render_gap_check(structured_data: dict) -> str:
    return (
        f"<h3>Issue</h3>{_paragraph(structured_data['issue'])}"
        f"<h3>Explanation</h3>{_paragraph(structured_data['explanation'])}"
        f"<h3>Recommendation</h3>{_paragraph(structured_data['recommendation'])}"
    )


def _render_rewrite(structured_data: dict) -> str:
    steps = "".join(f"<li>{escape(step)}</li>" for step in structured_data["procedure"])
    return (
        f"<h2>Purpose</h2>{_paragraph(structured_data['purpose'])}"
        f"<h2>Scope</h2>{_paragraph(structured_data['scope'])}"
        f"<h2>Responsibilities</h2>{_paragraph(structured_data['responsibilities'])}"
        f"<h2>Procedure</h2><ol>{steps}</ol>"
        f"<h2>Documentation</h2>{_paragraph(structured_data['documentation'])}"
    )


def _render_improve(structured_data: dict) -> str:
    return (
        f"<h3>Improved Version</h3>{_paragraph(structured_data['improved_version'])}"
        f"<h3>Reason for Improvement</h3>{_paragraph(structured_data['reason_for_improvement'])}"
    )


def _call_action_llm(runtime: Any, prompt: str) -> str:
    parser = StrOutputParser()
    try:
        return (runtime.llm | parser).invoke(prompt)
    except Exception:
        return (runtime.fallback_llm | parser).invoke(prompt)


def _render_dynamic_text(text: str) -> str:
    lines = [line.strip() for line in re.split(r"\r?\n+", text or "") if line.strip()]
    if not lines:
        return "<p>No suggestion returned.</p>"
    return "".join(f"<p>{escape(line)}</p>" for line in lines)


def _render_dynamic_gap_check(gaps: list[dict[str, str]]) -> str:
    if not gaps:
        return "<p>No compliance gaps identified for the selected text.</p>"
    return "".join(
        (
            f"<h3>Issue</h3>{_paragraph(gap.get('issue', ''))}"
            f"<h3>Explanation</h3>{_paragraph(gap.get('explanation', ''))}"
            f"<h3>Recommendation</h3>{_paragraph(gap.get('recommendation', ''))}"
        )
        for gap in gaps
    )


def _build_action_request(payload: AIActionRequest) -> ActionRequest:
    return ActionRequest(
        document_id=payload.sop_title or "editor-document",
        section_id=(payload.section_name or "selected-text").lower().replace(" ", "-"),
        sop_title=payload.sop_title or "Untitled SOP",
        section_title=payload.section_name or "Selected text",
        section_type=payload.section_type or "Selected Text",
        section_text=payload.text,
    )


def _build_gap_check_retrieval_query(request: ActionRequest) -> str:
    parts = [
        f"SOP: {request.sop_title}",
        f"Section: {request.section_title}",
        f"Type: {request.section_type}",
        request.section_text,
    ]
    return "\n".join(part.strip() for part in parts if part and part.strip())


def _run_dynamic_ai_action(payload: AIActionRequest, action: str) -> AIActionResponse:
    runtime = _get_action_runtime()
    request = _build_action_request(payload)
    retrieval_query = _build_gap_check_retrieval_query(request) if action == "gap_check" else request.section_text
    raw_docs = runtime.retriever.invoke(retrieval_query)
    reranked = runtime.reranker.rerank_top_n(retrieval_query, raw_docs, 3)
    context = format_chunks(reranked)

    if action == "improve":
        prompt = build_improve_prompt(request, context)
        parsed = parse_with_retry(
            raw=_call_action_llm(runtime, prompt),
            schema=ImproveResponse,
            prompt=prompt,
            call_llm=lambda retry_prompt: _call_action_llm(runtime, retry_prompt),
            audit_log=[],
        )
        return AIActionResponse(
            action="improve",
            original_text=request.section_text,
            suggested_text=_render_dynamic_text(parsed.improved_text),
            explanation="Text verbessert / Text improved.",
            structured_data={
                "improved_text": parsed.improved_text,
                "improved_version": parsed.improved_text,
            },
        )

    if action == "rewrite":
        prompt = build_rewrite_prompt(request, context)
        parsed = parse_with_retry(
            raw=_call_action_llm(runtime, prompt),
            schema=RewriteResponse,
            prompt=prompt,
            call_llm=lambda retry_prompt: _call_action_llm(runtime, retry_prompt),
            audit_log=[],
        )
        return AIActionResponse(
            action="rewrite",
            original_text=request.section_text,
            suggested_text=_render_dynamic_text(parsed.rewritten_text),
            explanation="Text neu formuliert / Text rewritten.",
            structured_data={
                "rewritten_text": parsed.rewritten_text,
            },
        )

    if action == "gap_check":
        prompt = build_gap_check_prompt(request, context)
        parsed = parse_with_retry(
            raw=_call_action_llm(runtime, prompt),
            schema=GapCheckResponse,
            prompt=prompt,
            call_llm=lambda retry_prompt: _call_action_llm(runtime, retry_prompt),
            audit_log=[],
        )
        return AIActionResponse(
            action="gap_check",
            original_text=request.section_text,
            suggested_text=_render_dynamic_text(parsed.analysis),
            explanation="Compliance-Lückenanalyse abgeschlossen / Compliance gap analysis completed.",
            structured_data={
                "analysis": parsed.analysis,
            },
        )

    raise HTTPException(status_code=400, detail=f"Action '{action}' is not supported.")


def _fallback_gap_check(payload: AIActionRequest) -> AIActionResponse:
    runtime = _get_action_runtime()
    request = _build_action_request(payload)
    prompt = build_gap_check_prompt(request, "Kein relevanter Kontext verfügbar. / No relevant context found.")
    raw = _call_action_llm(runtime, prompt)
    parsed = parse_with_retry(
        raw=raw,
        schema=GapCheckResponse,
        prompt=prompt,
        call_llm=lambda retry_prompt: _call_action_llm(runtime, retry_prompt),
        audit_log=[],
    )
    return AIActionResponse(
        action="gap_check",
        original_text=_clean_text(payload.text),
        suggested_text=_render_dynamic_text(parsed.analysis),
        explanation="Compliance-Lückenanalyse abgeschlossen / Compliance gap analysis completed.",
        structured_data={"analysis": parsed.analysis},
    )


def _fallback_rewrite(payload: AIActionRequest) -> AIActionResponse:
    runtime = _get_action_runtime()
    request = _build_action_request(payload)
    prompt = build_rewrite_prompt(request, "Kein relevanter Kontext verfügbar. / No relevant context found.")
    raw = _call_action_llm(runtime, prompt)
    parsed = parse_with_retry(
        raw=raw,
        schema=RewriteResponse,
        prompt=prompt,
        call_llm=lambda retry_prompt: _call_action_llm(runtime, retry_prompt),
        audit_log=[],
    )
    return AIActionResponse(
        action="rewrite",
        original_text=_clean_text(payload.text),
        suggested_text=_render_dynamic_text(parsed.rewritten_text),
        explanation="Text neu formuliert / Text rewritten.",
        structured_data={"rewritten_text": parsed.rewritten_text},
    )


def _fallback_improve(payload: AIActionRequest) -> AIActionResponse:
    runtime = _get_action_runtime()
    request = _build_action_request(payload)
    prompt = build_improve_prompt(request, "Kein relevanter Kontext verfügbar. / No relevant context found.")
    raw = _call_action_llm(runtime, prompt)
    parsed = parse_with_retry(
        raw=raw,
        schema=ImproveResponse,
        prompt=prompt,
        call_llm=lambda retry_prompt: _call_action_llm(runtime, retry_prompt),
        audit_log=[],
    )
    return AIActionResponse(
        action="improve",
        original_text=_clean_text(payload.text),
        suggested_text=_render_dynamic_text(parsed.improved_text),
        explanation="Text verbessert / Text improved.",
        structured_data={"improved_text": parsed.improved_text},
    )


def _extract_selected_text_html(action: str, structured_data: dict, suggested_text: str) -> str:
    if action == "rewrite":
        return _render_dynamic_text(structured_data.get("rewritten_text") or suggested_text)
    if action == "improve":
        return _render_dynamic_text(structured_data.get("improved_text") or suggested_text)
    return suggested_text


@ai_router.post("/api/ai/action", response_model=AIActionResponse)
async def perform_ai_action(payload: AIActionRequest):
    """
    Perform a structured AI action on selected SOP text.
    The current implementation uses deterministic structured generation so the
    frontend can reliably support compare-and-confirm workflows.
    """
    action = _normalize_action(payload.action)
    payload.text = _clean_text(payload.text)
    if not payload.text:
        raise HTTPException(status_code=422, detail="Selected text is required.")

    try:
        return await asyncio.to_thread(_run_dynamic_ai_action, payload, action)
    except HTTPException:
        raise
    except Exception:
        if action == "gap_check":
            return _fallback_gap_check(payload)
        if action == "rewrite":
            return _fallback_rewrite(payload)
        if action == "improve":
            return _fallback_improve(payload)

    raise HTTPException(status_code=400, detail=f"Action '{payload.action}' is not supported.")


@ai_router.post("/api/ai/query")
async def query_ai(payload: dict):
    """
    Chatbot query endpoint integrated from the standalone chatbot module.
    """
    question = (payload.get("question") or payload.get("query") or "").strip()
    if not question:
        raise HTTPException(status_code=422, detail="question is required")

    category = payload.get("category")
    chat_history = payload.get("chat_history") or []

    if CHATBOT_USE_LOCAL_DB:
        return _build_local_db_chat_response(question, chat_history, category)

    db_fallback_response = _build_sop_db_fallback(question, chat_history)

    fallback_answer = (
        "Chatbot is taking longer than expected to fetch knowledge context. "
        "Please try again in a few seconds, or ask a more specific question "
        "(for example with an SOP/DEV/CAPA ID)."
    )

    try:
        rag = await asyncio.wait_for(
            asyncio.to_thread(_get_smart_rag_chain),
            timeout=CHAT_QUERY_TIMEOUT_SECONDS,
        )
        result = await asyncio.wait_for(
            asyncio.to_thread(
                rag.invoke,
                question,
                category,
                chat_history,
            ),
            timeout=CHAT_QUERY_TIMEOUT_SECONDS,
        )
    except (TimeoutError, asyncio.TimeoutError):
        if db_fallback_response is not None:
            return db_fallback_response
        return {
            "answer": fallback_answer,
            "sources": [],
            "citations": [],
            "suggestions": [
                "Try again in a few seconds",
                "Ask with an exact SOP/DEV/CAPA number",
                "Use a shorter, specific question",
            ],
            "retrieval_stats": {"timeout": True},
            "routed_to": "timeout-fallback",
        }
    except Exception:
        if db_fallback_response is not None:
            return db_fallback_response
        return {
            "answer": fallback_answer,
            "sources": [],
            "citations": [],
            "suggestions": [
                "Retry the same question",
                "Check chatbot credentials in backend .env",
                "Ask with a specific document ID",
            ],
            "retrieval_stats": {"error": True},
            "routed_to": "error-fallback",
        }

    citations = result.get("citations", [])
    sources = []
    for idx, c in enumerate(citations):
        ref = c.get("ref") or c.get("title") or f"source-{idx+1}"
        label = c.get("title") or c.get("ref") or "Source"
        source_type = (c.get("type") or "doc").lower()
        sources.append({"id": ref, "type": source_type, "label": label})

    response = {
        "answer": result.get("answer", ""),
        "sources": sources,
        "citations": citations,
        "suggestions": result.get("suggestions", []),
        "retrieval_stats": result.get("retrieval_stats", {}),
        "routed_to": result.get("routed_to", ""),
    }

    answer_text = (response.get("answer") or "").strip().lower()
    rag_weak = (
        not answer_text
        or "no relevant information found" in answer_text
        or "do not contain sufficient detail" in answer_text
    )
    if rag_weak and db_fallback_response is not None:
        return db_fallback_response

    return response
