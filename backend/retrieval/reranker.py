from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
from typing import List


class CrossEncoderReranker:
    """
    Cross-encoder reranker using ms-marco-MiniLM-L-6-v2.
    Scores each (query, passage) pair and returns top-N by relevance.
    """
    def __init__(self, top_n: int = 5):
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512,
        )
        self.top_n = top_n

    def _score_and_filter(self, query: str, docs: List[Document], top_n: int) -> List[Document]:
        """Core scoring logic shared by rerank() and rerank_top_n()."""
        if not docs:
            return []

        pairs  = [(query, doc.page_content) for doc in docs]
        scores = self.model.predict(pairs)

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

        # For cross-lingual / noisy queries, the cross-encoder can assign uniformly
        # low negative scores and degrade an otherwise good hybrid ranking. In that
        # case, keep the original retrieval order.
        if ranked and float(ranked[0][1]) < 0:
            fallback = docs[:top_n]
            for doc in fallback:
                doc.metadata["rerank_score"] = float("-inf")
            return fallback

        top = ranked[:top_n]
        for doc, score in top:
            doc.metadata["rerank_score"] = float(score)

        # Filter out very low scores to avoid noise
        filtered = [(doc, score) for doc, score in top if score > -5.0]
        if not filtered:
            filtered = top

        return [doc for doc, _ in filtered]

    def rerank(self, query: str, docs: List[Document]) -> List[Document]:
        """Rerank using the default top_n set at construction time."""
        return self._score_and_filter(query, docs, self.top_n)

    def rerank_top_n(self, query: str, docs: List[Document], top_n: int) -> List[Document]:
        """Rerank with a caller-specified top_n (used by FederatedRetriever per section)."""
        return self._score_and_filter(query, docs, top_n)
