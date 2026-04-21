import httpx
import hashlib
import os
from typing import List
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

def _make_deterministic_id(chunk_id: str) -> int:
    """Convert any chunk_id string into a deterministic integer for Qdrant."""
    return int(hashlib.md5(chunk_id.encode()).hexdigest(), 16) % (2**63 - 1)

def _flatten_content_json(content_json: dict) -> str:
    """Recursively walk a TipTap content_json tree and return plain-text."""
    if not content_json: return ""
    parts: List[str] = []
    def walk(node: dict):
        node_type = node.get("type", "")
        children  = node.get("content", [])
        if node_type == "text":
            parts.append(node.get("text", ""))
        elif node_type == "heading":
            level = node.get("attrs", {}).get("level", 2)
            inner = "".join(c.get("text", "") for c in children if c.get("type") == "text")
            parts.append(f"\n{'#' * level} {inner}\n")
        elif node_type == "paragraph":
            inner = "".join(c.get("text", "") for c in children if c.get("type") == "text")
            if inner.strip(): parts.append(inner + "\n")
        else:
            for child in children: walk(child)
    walk(content_json)
    return "".join(parts).strip()

class APIDataFetcher:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "").rstrip("/")
        self.endpoint_sops = os.getenv("ENDPOINT_SOPS", "/api/sops")
        self.headers = {"Accept": "application/json"}
        api_key = os.getenv("API_KEY")
        if api_key and api_key != "dummy_developer_key":
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def fetch_all(self, category: str = None) -> List[Document]:
        """Fetch all SOPs and process them from the flat list response."""
        docs: List[Document] = []
        async with httpx.AsyncClient(timeout=30) as client:
            print(f"Fetching full SOP archive from {self.base_url}{self.endpoint_sops}...")
            resp = await client.get(f"{self.base_url}{self.endpoint_sops}", headers=self.headers)
            resp.raise_for_status()
            items = resp.json()
            if not isinstance(items, list):
                items = items.get("results") or items.get("data") or []

            for item in items:
                version = item.get("current_version") or {}
                content = version.get("content_json") or {}
                text = _flatten_content_json(content)
                
                if not text:
                    text = f"{item.get('sop_number', 'SOP')} - {item.get('title', 'Untitled Document')}"

                source_id = item.get("sop_number") or str(item.get("id", ""))
                meta = {
                    "title": item.get("title", ""),
                    "sop_number": item.get("sop_number", ""),
                    "department": item.get("department", ""),
                    "status": version.get("external_status", ""),
                    "source_id": source_id,
                    "chunk_id": source_id,
                    "qdrant_id": _make_deterministic_id(source_id),
                    # Audit Vault - Preserve full metadata and audit trail
                    "full_metadata": version.get("metadata_json", {}),
                    "audit_trail": version.get("metadata_json", {}).get("auditTrail", []),
                }
                docs.append(Document(page_content=text, metadata=meta))
                
        print(f"Successfully processed {len(docs)} documents.")
        return docs
