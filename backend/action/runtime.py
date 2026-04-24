"""Runtime construction for SOP editor actions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from embeddings.embedder import get_embedder
from retrieval.hybrid_retriever import (
    HybridRetriever,
    rag_unified_enabled,
    unified_semantic_collection,
)
from retrieval.reranker import CrossEncoderReranker

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


def _get_action_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_ACTION_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
        temperature=temperature,
        max_output_tokens=int(os.getenv("GEMINI_ACTION_MAX_OUTPUT_TOKENS") or "4096"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=3,
        thinking_budget=int(os.getenv("GEMINI_ACTION_THINKING_BUDGET", "128")),
    )


def _get_action_fallback_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_ACTION_FALLBACK_MODEL", os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")),
        temperature=temperature,
        max_output_tokens=int(os.getenv("GEMINI_ACTION_MAX_OUTPUT_TOKENS") or "4096"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=2,
        thinking_budget=int(os.getenv("GEMINI_ACTION_FALLBACK_THINKING_BUDGET", "64")),
    )


def build_action_runtime(
    *,
    client: QdrantClient,
    embedder: object,
    reranker: CrossEncoderReranker,
    collection_name: str | None = None,
) -> ActionRuntime:
    if collection_name:
        collection = collection_name
    elif rag_unified_enabled():
        collection = unified_semantic_collection()
    else:
        collection = os.getenv("COLLECTION_SOPS", "docs_sops")
    vectorstore = QdrantVectorStore(client=client, collection_name=collection, embedding=embedder)
    retriever = HybridRetriever(
        vectorstore=vectorstore,
        client=client,
        collection_name=collection,
        dense_top_k=int(os.getenv("ACTION_DENSE_TOP_K", "8")),
        bm25_top_k=int(os.getenv("ACTION_BM25_TOP_K", "8")),
        final_top_k=int(os.getenv("ACTION_FINAL_TOP_K", "4")),
    )
    if rag_unified_enabled():
        retriever.category_filter = "sops"
    return ActionRuntime(
        client=client,
        embedder=embedder,
        reranker=reranker,
        retriever=retriever,
        llm=_get_action_llm(),
        fallback_llm=_get_action_fallback_llm(),
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
            llm=_get_action_llm(),
            fallback_llm=_get_action_fallback_llm(),
            collection_name=os.getenv("COLLECTION_SOPS", "docs_sops"),
        )
