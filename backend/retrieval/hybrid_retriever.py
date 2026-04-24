import os
import time
import numpy as np
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from rank_bm25 import BM25Okapi
from typing import Optional, List

# Module-level cache to store BM25 index and documents per collection, avoiding RAM leaks.
# Schema: { collection_name: {"docs": [...], "bm25": BM25Okapi, "time": float} }
_GLOBAL_BM25_CACHE = {}

# Federated "section" (router) -> payload entity_type in qa_semantic_chunks (semantic index).
SECTION_TO_ENTITY_TYPE = {
    "sops": "sop",
    "deviations": "deviation",
    "capas": "capa",
    "audits": "audit_finding",
    "decisions": "decision",
}


def rag_unified_enabled() -> bool:
    return os.getenv("RAG_UNIFIED_QDRANT", "true").strip().lower() == "true"


def unified_semantic_collection() -> str:
    return os.getenv("SEMANTIC_QDRANT_COLLECTION", "qa_semantic_chunks")

class HybridRetriever(BaseRetriever):
    vectorstore: QdrantVectorStore
    client: QdrantClient
    collection_name: str
    dense_top_k: int = 50
    bm25_top_k: int = 50
    dense_weight: float = 0.7
    bm25_weight: float = 0.3
    final_top_k: int = 20
    category_filter: Optional[str] = None
    metadata_filters: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True

    def _uses_unified_semantic_collection(self) -> bool:
        return rag_unified_enabled() and (self.collection_name or "") == unified_semantic_collection()

    def _target_entity_type(self) -> Optional[str]:
        if not self.category_filter:
            return None
        return SECTION_TO_ENTITY_TYPE.get(
            str(self.category_filter).strip().lower()
        )

    def _normalized_doc_type_filter(self) -> Optional[str]:
        if not self.category_filter:
            return None
        raw = str(self.category_filter).strip().lower()
        mapping = {
            "sops": "sop",
            "deviations": "deviation",
            "capas": "capa",
            "audits": "audit",
            "decisions": "decision",
        }
        return mapping.get(raw, raw)

    def _build_filter(self) -> Optional[Filter]:
        must_list = []

        # 1) Entity scope: per-doc collections use doc_type; unified semantic index uses entity_type
        if self.category_filter and self._uses_unified_semantic_collection():
            et = self._target_entity_type()
            if et:
                must_list.append(
                    FieldCondition(key="entity_type", match=MatchValue(value=et))
                )
        elif self.category_filter:
            normalized = self._normalized_doc_type_filter()
            must_list.append(
                Filter(
                    should=[
                        FieldCondition(key="doc_type", match=MatchValue(value=normalized)),
                        FieldCondition(key="metadata.doc_type", match=MatchValue(value=normalized)),
                    ]
                )
            )

        # 2) Arbitrary metadata / identifier filters
        if self.metadata_filters:
            for key, val in self.metadata_filters.items():
                if not val:
                    continue
                if str(key) == "ref_number":
                    must_list.append(
                        Filter(
                            should=[
                                FieldCondition(key="ref_number", match=MatchValue(value=val)),
                                FieldCondition(
                                    key="metadata.ref_number",
                                    match=MatchValue(value=val),
                                ),
                            ]
                        )
                    )
                elif str(key) == "department":
                    must_list.append(
                        Filter(
                            should=[
                                FieldCondition(key="department", match=MatchValue(value=val)),
                                FieldCondition(
                                    key="metadata.department",
                                    match=MatchValue(value=val),
                                ),
                            ]
                        )
                    )
                else:
                    must_list.append(
                        FieldCondition(key=str(key), match=MatchValue(value=val))
                    )

        if not must_list:
            return None

        return Filter(must=must_list)

    def _get_bm25_corpus(self) -> tuple[List[Document], BM25Okapi]:
        now = time.time()
        # Check cache: Only fetch from Qdrant if more than 5 minutes has passed (TTL: 300s)
        cache_entry = _GLOBAL_BM25_CACHE.get(self.collection_name)
        if cache_entry and (now - cache_entry["time"] < 300.0):
            return cache_entry["docs"], cache_entry["bm25"]

        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=100_000,
            with_payload=True,
            with_vectors=False,
        )
        docs, tokenized = [], []
        for p in points:
            pl = p.payload or {}
            text = (pl.get("page_content") or pl.get("chunk_text") or "").strip()
            nested = pl.get("metadata") or {}
            if not isinstance(nested, dict):
                nested = {}
            meta = {
                **nested,
                "qdrant_id": p.id,
            }
            for k in (
                "entity_type",
                "entity_id",
                "ref_number",
                "title",
                "department",
                "status",
                "version_id",
            ):
                if k in pl and pl[k] is not None and k not in meta:
                    meta[k] = pl[k]
            docs.append(Document(page_content=text, metadata=meta))
            tokenized.append(text.lower().split())
        
        if not docs:
            result_docs, result_bm25 = docs, BM25Okapi([["_empty_"]])
        else:
            result_docs, result_bm25 = docs, BM25Okapi(tokenized)
            
        # Update cache
        _GLOBAL_BM25_CACHE[self.collection_name] = {
            "docs": result_docs,
            "bm25": result_bm25,
            "time": now
        }
        
        return result_docs, result_bm25

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        filt = self._build_filter()
        try:
            dense_results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=self.dense_top_k,
                filter=filt,
            )
        except Exception:
            dense_results = []
        if dense_results:
            patched = []
            for d, s in dense_results:
                if not (d.page_content or "").strip():
                    alt = (d.metadata or {}).get("chunk_text")
                    if alt:
                        d = Document(page_content=str(alt), metadata=dict(d.metadata or {}))
                patched.append((d, s))
            dense_results = patched

        corpus_docs, bm25 = self._get_bm25_corpus()
        if not corpus_docs:
             return []

        # Apply metadata/category filter to BM25 corpus too, so dense and sparse
        # paths respect the same filtering rules.
        if self._uses_unified_semantic_collection() and self._target_entity_type():
            want = self._target_entity_type()
            filtered_corpus = [
                d
                for d in corpus_docs
                if str((d.metadata or {}).get("entity_type", "")) == want
            ]
        else:
            normalized = self._normalized_doc_type_filter()
            if not normalized:
                filtered_corpus = list(corpus_docs)
            else:
                filtered_corpus = [
                    d
                    for d in corpus_docs
                    if str((d.metadata or {}).get("doc_type", "")).lower() == normalized
                ]
        if self.category_filter:
            corpus_docs = filtered_corpus
            if not corpus_docs:
                return []
            bm25 = BM25Okapi([d.page_content.lower().split() for d in corpus_docs])
             
        bm25_scores = bm25.get_scores(query.lower().split())
        top_bm25_idx = np.argsort(bm25_scores)[::-1][:self.bm25_top_k]
        bm25_results = [
            (corpus_docs[i], float(bm25_scores[i])) for i in top_bm25_idx if i < len(corpus_docs)
        ]

        def norm(scores):
            s = np.array(scores)
            if len(s) == 0:
                return []
            mn, mx = s.min(), s.max()
            rng = mx - mn
            if rng < 1e-9:
                 return [1.0] * len(s)
            return (s - mn) / rng

        combined = {}
        if dense_results:
             d_scores = norm([s for _, s in dense_results])
             for (doc, _), ns in zip(dense_results, d_scores):
                 cid = doc.metadata.get("chunk_id", doc.page_content[:40])
                 combined[cid] = {
                     "doc": doc,
                     "score": self.dense_weight * ns,
                 }

        if bm25_results:
             b_scores = norm([s for _, s in bm25_results])
             for (doc, _), ns in zip(bm25_results, b_scores):
                 cid = doc.metadata.get("chunk_id", doc.page_content[:40])
                 if cid in combined:
                     combined[cid]["score"] += self.bm25_weight * ns
                 else:
                     combined[cid] = {
                         "doc": doc,
                         "score": self.bm25_weight * ns,
                     }

        ranked = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        return [r["doc"] for r in ranked[:self.final_top_k]]
