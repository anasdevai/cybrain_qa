from langchain_core.documents import Document
from typing import List, Tuple

MAX_CONTEXT_CHARS = 16_000  # ~4000 tokens — larger window for multi-SOP queries


def build_context(docs: List[Document]) -> Tuple[str, List[dict]]:
    """
    Build a numbered context string and a citations list from reranked documents.
    Each block is formatted with rich metadata so the LLM can reference SOP details.
    """
    context_parts = []
    citations = []
    total = 0

    for i, doc in enumerate(docs):
        snippet = doc.page_content.strip()
        if not snippet:
            continue
        if total + len(snippet) > MAX_CONTEXT_CHARS:
            break

        meta = doc.metadata
        sop_num   = meta.get("sop_number", "")
        title     = meta.get("title", "")
        dept      = meta.get("department", "")
        status    = meta.get("status", "")
        eff_date  = meta.get("effective_date", "")
        rev_date  = meta.get("review_date", "")
        rerank_sc = meta.get("rerank_score", 0.0)

        # Build a rich header for the context block so the LLM has full SOP context
        header_parts = []
        if sop_num:  header_parts.append(f"SOP: {sop_num}")
        if title:    header_parts.append(f"Title: {title}")
        if dept:     header_parts.append(f"Dept: {dept}")
        if status:   header_parts.append(f"Status: {status}")
        if eff_date: header_parts.append(f"Effective: {eff_date[:10]}")
        if rev_date: header_parts.append(f"Review: {rev_date[:10]}")

        header = " | ".join(header_parts) if header_parts else "SOP Document"

        context_parts.append(
            f"[{i}] {header}\n{snippet}"
        )

        citations.append({
            "index":        i,
            "content":      snippet,
            "metadata": {
                "sop_number":     sop_num,
                "title":          title,
                "department":     dept,
                "status":         status,
                "effective_date": eff_date,
                "review_date":    rev_date,
            },
            "rerank_score": round(float(rerank_sc), 4),
        })

        total += len(snippet)

    return "\n\n---\n\n".join(context_parts), citations
