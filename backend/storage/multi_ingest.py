"""
storage/multi_ingest.py
Reads all 5 entity types from the APIs, chunks them, and upserts each
into its own dedicated Qdrant collection.

Run with:
    uv run python -m storage.multi_ingest

DOES NOT modify any other existing files.
"""

import os
import asyncio
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore

from ingestion.multi_fetcher import fetch_all_entities
from ingestion.chunker import chunk_documents
from embeddings.embedder import get_embedder

load_dotenv()

# ---------------------------------------------------------------------------
# Collection map:  entity_key  ->  env-var collection name
# ---------------------------------------------------------------------------
COLLECTION_MAP = {
    "sops":       os.getenv("COLLECTION_SOPS",       "docs_sops"),
    "deviations": os.getenv("COLLECTION_DEVIATIONS", "docs_deviations"),
    "capas":      os.getenv("COLLECTION_CAPAS",       "docs_capas"),
    "decisions":  os.getenv("COLLECTION_DECISIONS",   "docs_decisions"),
    "audits":     os.getenv("COLLECTION_AUDITS",       "docs_audits"),
}


async def run_multi_ingestion():
    """
    Full pipeline:
      1. Fetch all entity documents in parallel from the 5 API endpoints.
      2. Chunk each group using the existing chunker.
      3. Upsert each group into its own Qdrant collection.
    """
    qdrant_url     = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY") or None

    # Shared Qdrant client & embedder (re-used across all collections)
    client   = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    embedder = get_embedder()

    print("\n=== Step 1: Fetching all entity data ===")
    entity_docs = await fetch_all_entities()

    for entity_key, collection_name in COLLECTION_MAP.items():
        raw_docs = entity_docs.get(entity_key, [])
        if not raw_docs:
            print(f"\n[{entity_key}] No documents - skipping.")
            continue

        print(f"\n=== Step 2: Chunking [{entity_key}] ({len(raw_docs)} docs) ===")
        chunks = chunk_documents(raw_docs)
        print(f"  Produced {len(chunks)} chunks -> collection: '{collection_name}'")

        print(f"=== Step 3: Upserting [{entity_key}] into Qdrant ===")
        await QdrantVectorStore.afrom_documents(
            documents=chunks,
            embedding=embedder,
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=collection_name,
            force_recreate=True,        # wipe + recreate on every run (idempotent)
        )
        print(f"  [OK] {len(chunks)} chunks upserted into '{collection_name}'")

    print("\n=== Multi-ingestion complete ===")


if __name__ == "__main__":
    asyncio.run(run_multi_ingestion())
