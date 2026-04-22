"""
retrieval/federated_retriever.py

Runs a HybridRetriever against every entity collection in parallel,
then reranks the results within each section independently.

Returns a dict:
    {
        "sops":       [Document, ...],
        "deviations": [Document, ...],
        "capas":      [Document, ...],
        "audits":     [Document, ...],
        "decisions":  [Document, ...],
    }
"""

import asyncio
from typing import Dict, List

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker


# Number of top results kept per section after reranking
SECTION_TOP_N = {
    "sops":       5,
    "deviations": 4,
    "capas":      3,
    "audits":     3,
    "decisions":  3,
}


class FederatedRetriever:
    """
    Queries all 5 entity collections with Hybrid Search (Dense + BM25)
    and reranks each section independently with a Cross-Encoder.
    """

    def __init__(
        self,
        client: QdrantClient,
        vectorstores: Dict[str, QdrantVectorStore],
        reranker: CrossEncoderReranker,
    ):
        self.reranker = reranker
        # Build one HybridRetriever per collection
        self.retrievers: Dict[str, HybridRetriever] = {
            section: HybridRetriever(
                vectorstore=vs,
                client=client,
                collection_name=collection_name,
                dense_top_k=20,
                bm25_top_k=20,
                final_top_k=10,
            )
            for (section, vs), collection_name in zip(
                vectorstores.items(),
                vectorstores.keys(),   # collection names injected below
            )
        }
        # Override collection names properly
        collection_map = {
            "sops":       "docs_sops",
            "deviations": "docs_deviations",
            "capas":      "docs_capas",
            "audits":     "docs_audits",
            "decisions":  "docs_decisions",
        }
        for section, retriever in self.retrievers.items():
            retriever.collection_name = collection_map[section]

    def _retrieve_section(self, section: str, query: str, metadata_filters: dict = None) -> List[Document]:
        """Run hybrid retrieval for one section (blocking, safe for threads)."""
        try:
            retriever = self.retrievers[section]
            retriever.metadata_filters = metadata_filters
            return retriever.invoke(query)
        except Exception as e:
            print(f"  [federated] Warning: retrieval failed for '{section}': {e}")
            return []

    def search(self, query: str, metadata_filters: dict = None) -> Dict[str, List[Document]]:
        """
        Run all 5 retrievers in parallel via a thread pool,
        then rerank each section independently.
        Returns dict of section -> reranked documents.
        """
        sections = list(self.retrievers.keys())

        # Use asyncio.to_thread to run each blocking retriever in parallel
        async def _gather():
            tasks = [
                asyncio.to_thread(self._retrieve_section, section, query, metadata_filters)
                for section in sections
            ]
            return await asyncio.gather(*tasks)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already inside an event loop (FastAPI context)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    raw_results = list(pool.map(
                        lambda s: self._retrieve_section(s, query, metadata_filters),
                        sections
                    ))
            else:
                raw_results = loop.run_until_complete(_gather())
        except RuntimeError:
            raw_results = [self._retrieve_section(s, query, metadata_filters) for s in sections]

        # Rerank each section independently
        reranked: Dict[str, List[Document]] = {}
        for section, docs in zip(sections, raw_results):
            top_n = SECTION_TOP_N.get(section, 3)
            if docs:
                reranked[section] = self.reranker.rerank_top_n(query, docs, top_n)
            else:
                reranked[section] = []
            print(f"  [federated] {section}: {len(docs)} retrieved -> {len(reranked[section])} after rerank")

        return reranked
