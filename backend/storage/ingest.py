from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from ingestion.api_fetcher import APIDataFetcher
from storage.qdrant_setup import create_collection
from embeddings.embedder import get_embedder


async def run_ingestion(category: str = None):
    qdrant_url     = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection     = os.getenv("COLLECTION_SOPS", "docs_sops")

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    create_collection(client, collection)

    # ---------- Fetch + clean ----------
    fetcher  = APIDataFetcher()
    # Chunks come back already cleaned — no extra chunking needed
    chunks   = await fetcher.fetch_all(category=category)
    print(f"Fetched and cleaned {len(chunks)} chunks from API")

    if not chunks:
        print("No chunks to ingest. Verify API_BASE_URL and the endpoint response.")
        return

    # ---------- Embed ----------
    embedder   = get_embedder()
    texts      = [c.page_content for c in chunks]
    embeddings = embedder.embed_documents(texts)
    print(f"Generated {len(embeddings)} dense embeddings")

    # ---------- Build Qdrant points ----------
    points = []
    for chunk, emb in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id     = chunk.metadata["qdrant_id"],
                vector = emb,
                payload = {
                    # Searchable text
                    "page_content": chunk.page_content,
                    # Flat meaningful metadata only
                    "title":          chunk.metadata.get("title", ""),
                    "sop_number":     chunk.metadata.get("sop_number", ""),
                    "department":     chunk.metadata.get("department", ""),
                    "status":         chunk.metadata.get("status", ""),
                    "effective_date": chunk.metadata.get("effective_date", ""),
                    "review_date":    chunk.metadata.get("review_date", ""),
                    "chunk_id":       chunk.metadata.get("chunk_id", ""),
                    # Keep nested metadata for LangChain retriever compatibility
                    "metadata": chunk.metadata,
                }
            )
        )

    # ---------- Upsert in batches ----------
    print(f"Upserting {len(points)} points into '{collection}'...")
    batch_size = 64
    for i in range(0, len(points), batch_size):
        client.upsert(collection_name=collection, points=points[i:i+batch_size])

    print(f"Done. Successfully ingested {len(points)} SOP chunks into '{collection}'.")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
