"""Runtime construction for SOP editor actions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from backend.chain.rag_chain import get_fallback_llm, get_llm
from backend.embeddings.embedder import get_embedder
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


@dataclass
class ActionRuntime:
    client: QdrantClient
    embedder: object
    reranker: CrossEncoderReranker
    retriever: HybridRetriever
    llm: object
    fallback_llm: object
    collection_name: str


class _NoContextRetriever:
    dense_weight = 0.5
    bm25_weight = 0.5

    def invoke(self, _query: str):
        return []


class _NoopReranker:
    def rerank_top_n(self, _query: str, docs, _top_n: int):
        return docs


def build_action_runtime(
    *,
    client: QdrantClient,
    embedder: object,
    reranker: CrossEncoderReranker,
    collection_name: str | None = None,
) -> ActionRuntime:
    collection = collection_name or os.getenv("COLLECTION_SOPS", "docs_sops")
    vectorstore = QdrantVectorStore(client=client, collection_name=collection, embedding=embedder)
    retriever = HybridRetriever(
        vectorstore=vectorstore,
        client=client,
        collection_name=collection,
        dense_top_k=20,
        bm25_top_k=20,
        final_top_k=8,
    )
    return ActionRuntime(
        client=client,
        embedder=embedder,
        reranker=reranker,
        retriever=retriever,
        llm=get_llm(),
        fallback_llm=get_fallback_llm(),
        collection_name=collection,
    )


def create_action_runtime() -> ActionRuntime:
    try:
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        embedder = get_embedder()
        reranker = CrossEncoderReranker(top_n=5)
        return build_action_runtime(client=client, embedder=embedder, reranker=reranker)
    except Exception:
        # Keep editor actions responsive even when Qdrant is unavailable.
        return ActionRuntime(
            client=None,
            embedder=None,
            reranker=_NoopReranker(),
            retriever=_NoContextRetriever(),
            llm=get_llm(),
            fallback_llm=get_fallback_llm(),
            collection_name=os.getenv("COLLECTION_SOPS", "docs_sops"),
        )
