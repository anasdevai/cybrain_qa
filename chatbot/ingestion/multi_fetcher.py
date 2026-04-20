"""
ingestion/multi_fetcher.py
Fetches data from all 5 entity-specific API endpoints in parallel,
cleans and normalises each record into a LangChain Document,
ready to be chunked and upserted into separate Qdrant collections.

DOES NOT modify any existing files.
"""

import os
import asyncio
from typing import List

import httpx
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
HEADERS = {
    "Accept": "application/json",
}
api_key = os.getenv("API_KEY", "")
if api_key and api_key != "dummy_developer_key":
    HEADERS["Authorization"] = f"Bearer {api_key}"


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _flatten_content_json(content_json: dict) -> str:
    """
    Recursively walk a TipTap / ProseMirror content_json tree and
    return a single plain-text string preserving heading context.
    """
    if not content_json:
        return ""

    parts: List[str] = []

    def walk(node: dict):
        node_type = node.get("type", "")
        children  = node.get("content", [])

        if node_type == "text":
            parts.append(node.get("text", ""))
            return

        if node_type == "heading":
            level  = node.get("attrs", {}).get("level", 2)
            prefix = "#" * level + " "
            inner  = "".join(c.get("text", "") for c in children if c.get("type") == "text")
            parts.append(f"\n{prefix}{inner}\n")
            return

        if node_type == "paragraph":
            inner = "".join(c.get("text", "") for c in children if c.get("type") == "text")
            if inner.strip():
                parts.append(inner + "\n")
            return

        # Recurse into any other container node
        for child in children:
            walk(child)

    walk(content_json)
    return "".join(parts).strip()


# ---------------------------------------------------------------------------
# Per-entity cleaners — returns a LangChain Document or None
# ---------------------------------------------------------------------------

def _clean_sop(item: dict) -> Document | None:
    version      = item.get("current_version") or {}
    content_json = version.get("content_json") or {}
    meta_json    = version.get("metadata_json") or {}
    sop_meta     = meta_json.get("sopMetadata") or {}

    # Flatten the TipTap JSON into plain text
    text = _flatten_content_json(content_json)

    # If content_json only has a generic placeholder, build text from title
    if not text or "Technical documentation for" in text:
        text = (
            f"{item.get('sop_number', '')} - {item.get('title', '')}\n"
            f"Department: {item.get('department', '')}\n"
        )

    return Document(
        page_content=text,
        metadata={
            "doc_type":   "sop",
            "source_id":  item.get("sop_number") or str(item.get("id", "")),
            "ref_number": item.get("sop_number", ""),
            "title":      item.get("title", ""),
            "department": item.get("department", ""),
            "status":     version.get("external_status", ""),
            "risk_level": sop_meta.get("riskLevel", ""),
            # Audit Vault Snapshots
            "full_metadata": item,
            "audit_trail": meta_json.get("auditTrail", []),
        },
    )


def _clean_deviation(item: dict) -> Document | None:
    lines = [
        f"Deviation: {item.get('deviation_number', '')} - {item.get('title', '')}",
        f"Description: {item.get('description_text', '')}",
        f"Root Cause: {item.get('root_cause_text', '')}",
        f"Impact Level: {item.get('impact_level', '')}",
        f"Status: {item.get('external_status', '')}",
    ]
    text = "\n".join(l for l in lines if l.split(": ", 1)[-1].strip())

    return Document(
        page_content=text,
        metadata={
            "doc_type":     "deviation",
            "source_id":    item.get("deviation_number") or str(item.get("id", "")),
            "ref_number":   item.get("deviation_number", ""),
            "title":        item.get("title", ""),
            "status":       item.get("external_status", ""),
            "impact_level": item.get("impact_level", ""),
            # Audit Vault Snapshots
            "full_metadata": item,
            "audit_trail": item.get("audit_trail") or item.get("auditTrail") or [],
        },
    )


def _clean_capa(item: dict) -> Document | None:
    lines = [
        f"CAPA: {item.get('capa_number', '')} - {item.get('title', '')}",
        f"Action: {item.get('action_text', '')}",
        f"Status: {item.get('external_status', '')}",
    ]
    text = "\n".join(l for l in lines if l.split(": ", 1)[-1].strip())

    return Document(
        page_content=text,
        metadata={
            "doc_type":   "capa",
            "source_id":  item.get("capa_number") or str(item.get("id", "")),
            "ref_number": item.get("capa_number", ""),
            "title":      item.get("title", ""),
            "status":     item.get("external_status", ""),
            # Audit Vault Snapshots
            "full_metadata": item,
            "audit_trail": item.get("audit_trail") or item.get("auditTrail") or [],
        },
    )


def _clean_decision(item: dict) -> Document | None:
    lines = [
        f"Decision: {item.get('decision_number', '')} - {item.get('title', '')}",
        f"Statement: {item.get('decision_statement', '')}",
        f"Rationale: {item.get('rationale_text', '')}",
    ]
    text = "\n".join(l for l in lines if l.split(": ", 1)[-1].strip())

    return Document(
        page_content=text,
        metadata={
            "doc_type":   "decision",
            "source_id":  item.get("decision_number") or str(item.get("id", "")),
            "ref_number": item.get("decision_number", ""),
            "title":      item.get("title", ""),
            "status":     "",
            # Audit Vault Snapshots
            "full_metadata": item,
            "audit_trail": item.get("audit_trail") or item.get("auditTrail") or [],
        },
    )


def _clean_audit(item: dict) -> Document | None:
    lines = [
        f"Audit Finding: {item.get('finding_number', '')}",
        f"Finding: {item.get('finding_text', '')}",
        f"Acceptance: {item.get('acceptance_status', '')}",
    ]
    text = "\n".join(l for l in lines if l.split(": ", 1)[-1].strip())

    return Document(
        page_content=text,
        metadata={
            "doc_type":   "audit",
            "source_id":  item.get("finding_number") or str(item.get("id", "")),
            "ref_number": item.get("finding_number", ""),
            "title":      item.get("finding_number", "Audit Finding"),
            "status":     item.get("acceptance_status", ""),
            # Audit Vault Snapshots
            "full_metadata": item,
            "audit_trail": item.get("audit_trail") or item.get("auditTrail") or [],
        },
    )


# ---------------------------------------------------------------------------
# Async HTTP helpers
# ---------------------------------------------------------------------------

async def _fetch_json(client: httpx.AsyncClient, path: str) -> list:
    url = f"{BASE_URL}{path}"
    resp = await client.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else data.get("results", data.get("data", []))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def fetch_all_entities() -> dict[str, List[Document]]:
    """
    Fetches all 5 entity types from their API endpoints in parallel.
    Returns a dict:  { "sops": [...], "deviations": [...], ... }
    Each value is a list of LangChain Documents ready for chunking.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        sops_raw, devs_raw, capas_raw, decisions_raw, audits_raw = await asyncio.gather(
            _fetch_json(client, "/api/sops"),
            _fetch_json(client, "/api/deviations"),
            _fetch_json(client, "/api/capas"),
            _fetch_json(client, "/api/decisions"),
            _fetch_json(client, "/api/audits"),
        )

    def _safe_clean(cleaner, item, entity_type):
        try:
            return cleaner(item)
        except Exception as e:
            print(f"  [ERROR] Failed to clean {entity_type} item {item.get('id')}: {e}")
            return None

    result = {
        "sops":       [d for item in sops_raw      if (d := _safe_clean(_clean_sop, item, "sop"))       is not None],
        "deviations": [d for item in devs_raw       if (d := _safe_clean(_clean_deviation, item, "deviation")) is not None],
        "capas":      [d for item in capas_raw      if (d := _safe_clean(_clean_capa, item, "capa"))      is not None],
        "decisions":  [d for item in decisions_raw  if (d := _safe_clean(_clean_decision, item, "decision"))  is not None],
        "audits":     [d for item in audits_raw     if (d := _safe_clean(_clean_audit, item, "audit"))     is not None],
    }

    for key, docs in result.items():
        print(f"  [{key}] fetched & cleaned {len(docs)} documents")

    return result


if __name__ == "__main__":
    data = asyncio.run(fetch_all_entities())
    for k, v in data.items():
        print(f"  {k}: {len(v)} docs | sample: {v[0].page_content[:80] if v else 'empty'}")
