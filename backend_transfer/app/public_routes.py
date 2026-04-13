"""
public_routes.py
================
Stage 1 — SOP Chatbot Data Provisioning API

Purpose:
    Expose clean, minimal read-only JSON endpoints so another developer can
    consume SOP document data for LLM/RAG chatbot testing.

Design decisions:
    - All routes are under /api/public/* to isolate from editor routes.
    - No mutation endpoints — everything here is GET-only.
    - content_json (TipTap tree) is flattened into sections[] at the API layer.
    - Only effective SOPs are returned by default (chatbot-safe default).
    - Internal fields (tenant_id, external_id, raw DB IDs) are stripped.
    - knowledge_chunks table is used for the /chunks endpoints.
    - source_path is synthesised as "sop_number/version_number" since there is
      no file-system path stored — the SOP lives entirely in the database.

Fields excluded from all public responses:
    - tenant_id      (internal multi-tenancy; must never leak)
    - external_id    (internal sync key; not meaningful to API consumer)
    - created_at     (DB audit; not relevant to chatbot)
    - updated_at     (DB audit; not relevant to chatbot)
    - superseded_by_version_id  (internal version graph)
    - block_id       (TipTap internal node ID)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .database import get_db
from .models import SOP, SOPVersion, KnowledgeChunk
import uuid
import math

# ─────────────────────────────────────────
# Router
# ─────────────────────────────────────────

public_router = APIRouter(prefix="/api/public", tags=["Public Chatbot API"])

# Fixed tenant for this dev/seed environment
FIXED_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

# ─────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────

def _source_path(sop: SOP, version: SOPVersion) -> str:
    """
    Synthesise a stable, human-readable source path for the SOP.
    Format: {sop_number}/v{version_number}
    Example: SOP-QA-042/v2
    """
    return f"{sop.sop_number}/v{version.version_number}"


def _tiptap_to_sections(content_json: dict) -> list[dict]:
    """
    Flatten a TipTap JSON document tree into a list of sections.

    TipTap structure:
        { type: "doc", content: [ nodes... ] }

    Each top-level heading becomes a section boundary.
    Paragraphs/lists under a heading are accumulated into that section's text.

    Returns:
        [
          { path, page_start, page_end, text }
        ]
    where:
        path       = heading text or "introduction" for pre-heading content
        page_start = 1  (no page tracking in TipTap; always 1 for DB-stored docs)
        page_end   = 1
        text       = full plain-text content of that section
    """
    if not content_json or not isinstance(content_json, dict):
        return []

    nodes = content_json.get("content", [])
    sections = []
    current_path = "introduction"
    current_lines = []

    def extract_text(node: dict) -> str:
        """Recursively extract plain text from any TipTap node."""
        if node.get("type") == "text":
            return node.get("text", "")
        texts = []
        for child in node.get("content", []):
            texts.append(extract_text(child))
        return " ".join(filter(None, texts))

    for node in nodes:
        node_type = node.get("type", "")

        if node_type == "heading":
            # Flush current section before starting a new one
            if current_lines:
                sections.append({
                    "path": current_path,
                    "page_start": 1,
                    "page_end": 1,
                    "text": "\n".join(current_lines).strip(),
                })
            current_path = extract_text(node).strip() or "section"
            current_lines = []

        elif node_type in ("paragraph", "bulletList", "orderedList"):
            text = extract_text(node).strip()
            if text:
                current_lines.append(text)

        elif node_type == "table":
            # Flatten table rows into lines
            for row in node.get("content", []):
                cells = []
                for cell in row.get("content", []):
                    cell_text = extract_text(cell).strip()
                    if cell_text:
                        cells.append(cell_text)
                if cells:
                    current_lines.append(" | ".join(cells))

    # Flush last section
    if current_lines:
        sections.append({
            "path": current_path,
            "page_start": 1,
            "page_end": 1,
            "text": "\n".join(current_lines).strip(),
        })

    return sections


def _estimate_tokens(text: str) -> int:
    """
    Rough token estimate: ~0.75 tokens per word (GPT-style tokenisation heuristic).
    For exact token counts the consumer should use their own tokeniser.
    """
    word_count = len(text.split())
    return math.ceil(word_count / 0.75)


def _build_public_sop_summary(sop: SOP, version: SOPVersion) -> dict:
    """Build the document-level public response (no sections, no chunks)."""
    return {
        "doc_id": str(sop.id),
        "sop_number": sop.sop_number,
        "title": sop.title,
        "department": sop.department,
        "source_path": _source_path(sop, version),
        "version": version.version_number,
        "status": version.external_status or "draft",
        "is_active": sop.is_active,
        "current_version_id": str(version.id),
        "effective_date": version.effective_date.isoformat() if version.effective_date else None,
        "review_date": version.review_date.isoformat() if version.review_date else None,
    }


def _get_active_version(sop: SOP, db: Session) -> SOPVersion | None:
    """Return the current version for an SOP, or None."""
    if not sop.current_version_id:
        return None
    return db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()


# ─────────────────────────────────────────
# Endpoint 1: List all effective SOPs
# ─────────────────────────────────────────

@public_router.get(
    "/sops",
    summary="List all effective SOP documents",
    response_description="Array of SOP document summaries",
)
def list_public_sops(
    status: str | None = Query(
        default="effective",
        description="Filter by version status. Default: 'effective'. Use 'all' to return every status.",
    ),
    db: Session = Depends(get_db),
):
    """
    Return a list of SOP documents available for chatbot use.

    Default behaviour:
    - Only returns SOPs whose current version status is 'effective'.
    - Pass `?status=all` to return every SOP regardless of status.
    - Pass `?status=draft` to return only drafts, etc.

    Fields returned per SOP:
    - doc_id, sop_number, title, department, source_path,
      version, status, is_active, current_version_id,
      effective_date, review_date
    """
    sops = db.query(SOP).filter(
        SOP.tenant_id == FIXED_TENANT_ID,
        SOP.is_active == True,
    ).all()

    results = []
    for sop in sops:
        version = _get_active_version(sop, db)
        if not version:
            continue
        # Apply status filter
        if status and status.lower() != "all":
            if (version.external_status or "draft").lower() != status.lower():
                continue
        results.append(_build_public_sop_summary(sop, version))

    return results


# ─────────────────────────────────────────
# Endpoint 6: GET /sops/full   (list, paginated)
# MUST be registered BEFORE /sops/{doc_id} so FastAPI matches it as a
# literal path instead of routing 'full' as a doc_id parameter.
# ─────────────────────────────────────────

@public_router.get(
    "/sops/full",
    summary="Get ALL SOPs in full combined format (paginated)",
    response_description=(
        "Paginated list of full SOP documents — "
        "each includes metadata, sections[], and chunks[]"
    ),
)
def list_full_sops(
    status: str = Query(
        default="effective",
        description=(
            "Filter by SOP version status. "
            "Default: 'effective'. Use 'all' to include every status."
        ),
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        default=10, ge=1, le=50,
        description="Results per page (1–50). Default: 10.",
    ),
    db: Session = Depends(get_db),
):
    """
    **Batch endpoint for loading all SOPs into a RAG index.**

    Returns each SOP in the same structure as `GET /api/public/sops/{doc_id}/full`.
    Paginated to keep response size manageable.

    Use cases:
    - Initial bulk embedding / indexing run
    - Verifying full corpus available to the chatbot
    - Diffing what changed between ingestion runs

    Filtering:
    - `?status=effective` (default) — only production-ready SOPs
    - `?status=all` — include drafts, obsolete, etc.
    - `?status=draft` — only drafts
    """
    all_sops = db.query(SOP).filter(
        SOP.tenant_id == FIXED_TENANT_ID,
        SOP.is_active == True,
    ).all()

    eligible: list[tuple[SOP, SOPVersion]] = []
    for sop in all_sops:
        version = _get_active_version(sop, db)
        if not version:
            continue
        if status.lower() != "all":
            if (version.external_status or "draft").lower() != status.lower():
                continue
        eligible.append((sop, version))

    total = len(eligible)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = eligible[start:end]

    results = [
        _build_full_sop_response(sop, version, db)
        for sop, version in page_items
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 1,
        "results": results,
    }


# ─────────────────────────────────────────
# Endpoint 2: Get one SOP with sections
# ─────────────────────────────────────────

@public_router.get(
    "/sops/{doc_id}",
    summary="Get one SOP document in normalized format with sections",
    response_description="Full SOP document with flattened sections for chatbot context",
)
def get_public_sop(doc_id: str, db: Session = Depends(get_db)):
    """
    Return a single SOP document in normalized document format.

    Includes:
    - All document-level metadata fields
    - sections[]: flattened from the TipTap content_json into
                  { path, page_start, page_end, text }

    This is the primary endpoint for feeding an SOP's full content
    into an LLM context window or for RAG indexing.
    """
    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid doc_id format")

    sop = db.query(SOP).filter(
        SOP.id == uid,
        SOP.tenant_id == FIXED_TENANT_ID,
    ).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    version = _get_active_version(sop, db)
    if not version:
        raise HTTPException(status_code=404, detail="SOP has no current version")

    summary = _build_public_sop_summary(sop, version)
    sections = _tiptap_to_sections(version.content_json or {})

    return {
        **summary,
        "sections": sections,
    }


# ─────────────────────────────────────────
# Endpoint 3: Get chunks for one SOP
# ─────────────────────────────────────────

@public_router.get(
    "/sops/{doc_id}/chunks",
    summary="Get all retrieval chunks for one SOP",
    response_description="Array of text chunks ready for embedding/RAG",
)
def get_public_sop_chunks(doc_id: str, db: Session = Depends(get_db)):
    """
    Return all knowledge_chunks for one SOP, ordered by chunk_order.

    If no pre-generated chunks exist in the knowledge_chunks table,
    chunks are auto-generated on-the-fly by splitting the SOP's sections
    (same as Endpoint 2 output) so the consumer always gets usable data.

    Fields per chunk:
    - chunk_id, doc_id, section_path, page_range, text, tokens_est
    - retrieval_metadata: { title, sop_number, version, status, source_path }
    """
    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid doc_id format")

    sop = db.query(SOP).filter(
        SOP.id == uid,
        SOP.tenant_id == FIXED_TENANT_ID,
    ).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    version = _get_active_version(sop, db)
    if not version:
        raise HTTPException(status_code=404, detail="SOP has no current version")

    source_p = _source_path(sop, version)
    retrieval_meta = {
        "title": sop.title,
        "sop_number": sop.sop_number,
        "version": version.version_number,
        "status": version.external_status or "draft",
        "source_path": source_p,
        "department": sop.department,
    }

    # ── Try pre-generated chunks from knowledge_chunks table ──
    db_chunks = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.entity_id == uid,
            KnowledgeChunk.entity_type == "sop",
        )
        .order_by(KnowledgeChunk.chunk_order.asc())
        .all()
    )

    if db_chunks:
        return [
            {
                "chunk_id": str(c.id),
                "doc_id": doc_id,
                "section_path": (c.metadata_json or {}).get("section_path", f"chunk_{c.chunk_order}"),
                "page_range": (c.metadata_json or {}).get("page_range", "1-1"),
                "text": c.chunk_text,
                "tokens_est": _estimate_tokens(c.chunk_text),
                "retrieval_metadata": retrieval_meta,
            }
            for c in db_chunks
        ]

    # ── Fallback: auto-generate chunks from sections on-the-fly ──
    # Each section becomes one chunk. This is Section-level chunking,
    # which is the correct default for Stage 1 SOP retrieval.
    sections = _tiptap_to_sections(version.content_json or {})
    auto_chunks = []
    for i, section in enumerate(sections):
        text = section["text"]
        if not text.strip():
            continue
        auto_chunks.append({
            "chunk_id": f"auto-{doc_id}-{i}",
            "doc_id": doc_id,
            "section_path": section["path"],
            "page_range": f"{section['page_start']}-{section['page_end']}",
            "text": text,
            "tokens_est": _estimate_tokens(text),
            "retrieval_metadata": retrieval_meta,
        })

    return auto_chunks


# ─────────────────────────────────────────
# Endpoint 4: Global chunk list with filter
# ─────────────────────────────────────────

@public_router.get(
    "/chunks",
    summary="List all chunks across all SOPs, filtered by status",
    response_description="Array of chunks from all SOPs for batch retrieval testing",
)
def list_all_chunks(
    status: str = Query(
        default="effective",
        description="Filter by SOP version status. Default: 'effective'.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Max chunks to return (1–500). Default: 100.",
    ),
    db: Session = Depends(get_db),
):
    """
    Return chunks from all SOPs matching the given status filter.

    Use this endpoint for:
    - Batch embedding generation
    - RAG retrieval testing across the full corpus
    - Verifying what data the chatbot will search over

    Default returns only 'effective' SOP chunks — the safest default
    for a production chatbot (avoids returning draft/obsolete content).
    """
    sops = db.query(SOP).filter(
        SOP.tenant_id == FIXED_TENANT_ID,
        SOP.is_active == True,
    ).all()

    all_chunks = []

    for sop in sops:
        version = _get_active_version(sop, db)
        if not version:
            continue
        if status.lower() != "all":
            if (version.external_status or "draft").lower() != status.lower():
                continue

        source_p = _source_path(sop, version)
        retrieval_meta = {
            "title": sop.title,
            "sop_number": sop.sop_number,
            "version": version.version_number,
            "status": version.external_status or "draft",
            "source_path": source_p,
            "department": sop.department,
        }

        # Try pre-generated chunks first
        db_chunks = (
            db.query(KnowledgeChunk)
            .filter(
                KnowledgeChunk.entity_id == sop.id,
                KnowledgeChunk.entity_type == "sop",
            )
            .order_by(KnowledgeChunk.chunk_order.asc())
            .all()
        )

        if db_chunks:
            for c in db_chunks:
                all_chunks.append({
                    "chunk_id": str(c.id),
                    "doc_id": str(sop.id),
                    "section_path": (c.metadata_json or {}).get("section_path", f"chunk_{c.chunk_order}"),
                    "page_range": (c.metadata_json or {}).get("page_range", "1-1"),
                    "text": c.chunk_text,
                    "tokens_est": _estimate_tokens(c.chunk_text),
                    "retrieval_metadata": retrieval_meta,
                })
        else:
            # Auto-generate from sections
            sections = _tiptap_to_sections(version.content_json or {})
            for i, section in enumerate(sections):
                text = section["text"]
                if not text.strip():
                    continue
                all_chunks.append({
                    "chunk_id": f"auto-{str(sop.id)}-{i}",
                    "doc_id": str(sop.id),
                    "section_path": section["path"],
                    "page_range": f"{section['page_start']}-{section['page_end']}",
                    "text": text,
                    "tokens_est": _estimate_tokens(text),
                    "retrieval_metadata": retrieval_meta,
                })

        if len(all_chunks) >= limit:
            break

    return all_chunks[:limit]


# ─────────────────────────────────────────
# Shared helpers for /full endpoints
# ─────────────────────────────────────────

def _build_sections_with_ids(content_json: dict) -> list[dict]:
    """
    Same as _tiptap_to_sections but adds a stable section_id field.
    section_id = "sec_{zero_padded_index}" so consumers can reference sections
    unambiguously in citations (e.g. "sec_00", "sec_01").
    """
    raw = _tiptap_to_sections(content_json)
    return [
        {
            "section_id": f"sec_{str(i).zfill(2)}",
            "path": s["path"],
            "page_start": s["page_start"],
            "page_end": s["page_end"],
            "text": s["text"],
        }
        for i, s in enumerate(raw)
    ]


def _build_chunks_for_full(
    sop: SOP,
    version: SOPVersion,
    sections: list[dict],
    db: Session,
) -> list[dict]:
    """
    Build the chunks[] array for the /full endpoint.
    Key difference from existing /chunks endpoint:
      - No doc_id field inside each chunk (already at top level of response)
      - metadata key (not retrieval_metadata) per the spec
      - Pulls from knowledge_chunks first, falls back to section-level auto-chunks
    """
    uid = sop.id
    doc_id_str = str(uid)
    status_val = version.external_status or "draft"
    meta = {
        "title": sop.title,
        "sop_number": sop.sop_number,
        "version": version.version_number,
        "status": status_val,
        "department": sop.department,
    }

    # ── Try pre-generated chunks from knowledge_chunks table ──
    db_chunks = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.entity_id == uid,
            KnowledgeChunk.entity_type == "sop",
        )
        .order_by(KnowledgeChunk.chunk_order.asc())
        .all()
    )

    if db_chunks:
        return [
            {
                "chunk_id": str(c.id),
                "section_path": (c.metadata_json or {}).get(
                    "section_path", f"chunk_{c.chunk_order}"
                ),
                "page_range": (c.metadata_json or {}).get("page_range", "1-1"),
                "text": c.chunk_text,
                "tokens_est": _estimate_tokens(c.chunk_text),
                "metadata": {
                    **meta,
                    # Merge any extra keys stored in chunk's own metadata_json
                    # (excluding internal fields we never expose)
                    **{
                        k: v
                        for k, v in (c.metadata_json or {}).items()
                        if k not in {
                            "section_path", "page_range",
                            "tenant_id", "block_id",
                        }
                    },
                },
            }
            for c in db_chunks
        ]

    # ── Fallback: one chunk per section (section-level chunking) ──
    chunks = []
    for i, sec in enumerate(sections):
        text = sec["text"]
        if not text.strip():
            continue
        chunks.append({
            "chunk_id": f"auto-{doc_id_str}-{i}",
            "section_path": sec["path"],
            "page_range": f"{sec['page_start']}-{sec['page_end']}",
            "text": text,
            "tokens_est": _estimate_tokens(text),
            "metadata": meta,
        })
    return chunks


def _build_full_sop_response(sop: SOP, version: SOPVersion, db: Session) -> dict:
    """
    Assemble the complete /full response for one SOP.
    Shared by both the single-doc and the list endpoint.
    """
    source_p = _source_path(sop, version)
    sections = _build_sections_with_ids(version.content_json or {})
    chunks = _build_chunks_for_full(sop, version, sections, db)

    return {
        "doc_id": str(sop.id),
        "sop_number": sop.sop_number,
        "title": sop.title,
        "department": sop.department,
        "status": version.external_status or "draft",
        "is_active": sop.is_active,
        "version": version.version_number,
        "current_version_id": str(version.id),
        "effective_date": (
            version.effective_date.isoformat() if version.effective_date else None
        ),
        "review_date": (
            version.review_date.isoformat() if version.review_date else None
        ),
        "source": {
            "system": sop.source_system or "cybrain-qs",
            "path": source_p,
        },
        "sections": sections,
        "chunks": chunks,
    }


# ─────────────────────────────────────────
# Endpoint 5: GET /sops/{doc_id}/full
# Single SOP — all data in one response
# ─────────────────────────────────────────

@public_router.get(
    "/sops/{doc_id}/full",
    summary="Get one SOP with metadata, sections, and chunks in a single response",
    response_description=(
        "Combined SOP document ready for LLM/RAG ingestion: "
        "metadata + sections[] + chunks[]"
    ),
)
def get_full_sop(doc_id: str, db: Session = Depends(get_db)):
    """
    **Stage 1 primary endpoint for LLM/RAG consumption.**

    Returns everything about one SOP in a single JSON object:

    - **metadata**: doc_id, sop_number, title, department, status, version, dates
    - **source**: system name and stable path string for citations
    - **sections[]**: TipTap content_json flattened to plain text blocks with section_id
    - **chunks[]**: retrieval-ready text units with token estimates and inline metadata

    Chunk sourcing priority:
    1. `knowledge_chunks` table (pre-generated, preferred)
    2. Auto-generated from sections (always available as fallback)

    Internal fields excluded: tenant_id, external_id, created_at, updated_at,
    block_id, raw content_json.
    """
    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid doc_id — must be a UUID")

    sop = db.query(SOP).filter(
        SOP.id == uid,
        SOP.tenant_id == FIXED_TENANT_ID,
    ).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    version = _get_active_version(sop, db)
    if not version:
        raise HTTPException(
            status_code=404,
            detail="SOP has no current version linked (current_version_id is null)",
        )

    return _build_full_sop_response(sop, version, db)

