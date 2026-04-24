"""
Rebuild LangChain-style Qdrant points (page_content + metadata) for the docs_* collections
used by SmartRAGChain / HybridRetriever — fetches from the local API, chunks, embeds
with the same BGE-M3 client as `embeddings/embedder.py`, upserts to Qdrant.

Usage (API on 127.0.0.1:8000):
  python scripts/reindex_rag_vectorstores.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("API_BASE_URL", "http://127.0.0.1:8000")

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from embeddings.embedder import get_embedder
from ingestion.multi_fetcher import fetch_all_entities

try:
    from langchain_core.documents import Document
except ModuleNotFoundError:  # pragma: no cover
    print("langchain_core is required for Document; pip install langchain-core", file=sys.stderr)
    raise


def _chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    if len(t) <= size:
        return [t]
    out = []
    start = 0
    while start < len(t):
        end = min(len(t), start + size)
        out.append(t[start:end].strip())
        if end == len(t):
            break
        start = max(end - overlap, start + 1)
    return [x for x in out if x]


def _slim_metadata(meta: dict) -> dict:
    if not meta:
        return {}
    allow = (
        "doc_type",
        "source_id",
        "ref_number",
        "title",
        "department",
        "status",
        "risk_level",
    )
    return {k: meta[k] for k in allow if k in meta and meta[k] is not None}


def _split_document(doc: Document) -> list[Document]:
    parts = _chunk_text(doc.page_content)
    if not parts:
        return []
    m = _slim_metadata(dict(doc.metadata or {}))
    return [Document(page_content=p, metadata={**m, "chunk_id": f"{i}-{hash(p) & 0xFFFF :x}"}) for i, p in enumerate(parts)]


def main() -> None:
    mapping = [
        ("sops", os.getenv("COLLECTION_SOPS", "docs_sops")),
        ("deviations", os.getenv("COLLECTION_DEVIATIONS", "docs_deviations")),
        ("capas", os.getenv("COLLECTION_CAPAS", "docs_capas")),
        ("audits", os.getenv("COLLECTION_AUDITS", "docs_audits")),
        ("decisions", os.getenv("COLLECTION_DECISIONS", "docs_decisions")),
    ]
    url = os.environ.get("QDRANT_URL")
    if not url:
        raise SystemExit("QDRANT_URL is not set")

    data = asyncio.run(fetch_all_entities())
    client = QdrantClient(url=url, api_key=os.environ.get("QDRANT_API_KEY"))
    embedder = get_embedder()

    for section, col in mapping:
        docs: list[Document] = data.get(section) or []
        flat: list[Document] = []
        for d in docs:
            flat.extend(_split_document(d))
        if not flat:
            print(f"[{section}] no chunks; leave {col} as-is")
            continue

        texts = [d.page_content for d in flat]
        vectors = embedder.embed_documents(texts)
        if not vectors:
            print(f"[{section}] no vectors")
            continue
        dim = len(vectors[0])
        if client.collection_exists(collection_name=col):
            client.delete_collection(collection_name=col)
        client.create_collection(
            collection_name=col,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload={
                    "page_content": flat[i].page_content,
                    "metadata": flat[i].metadata,
                },
            )
            for i in range(len(flat))
        ]
        client.upsert(collection_name=col, points=points, wait=True)
        n = client.get_collection(col).points_count
        print(f"[{section}] {col} -> {n} points (from {len(docs)} docs, {len(flat)} chunks)")


if __name__ == "__main__":
    main()
