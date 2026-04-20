# Hybrid RAG Chatbot – Production PRD

## 1. Overview
A production-grade Hybrid Retrieval-Augmented Generation (RAG) chatbot designed to handle large-scale datasets (millions of documents) using semantic + keyword search, reranking, and metadata-aware retrieval.

## 2. Goals
- High accuracy retrieval (>=90% relevance @ top-5)
- Low latency (<3s total response time)
- Scalable to millions of documents
- Provide grounded answers with citations

## 3. Architecture

### Pipeline Flow
```
Data Sources (APIs / DB / Files)
        ↓
Ingestion Pipeline
        ↓
Chunking + Metadata
        ↓
Embedding (bge-small)
        ↓
Qdrant Storage
        ↓
---------------------------------
        ↓
User Query
        ↓
Query Embedding
        ↓
Hybrid Retrieval (Dense + BM25)
        ↓
Score Fusion
        ↓
Reranker (Cross Encoder)
        ↓
Top-K Context
        ↓
LLM (Gemini Flash)
        ↓
Answer + Citations
```

## 4. Tech Stack
- LangChain
- Qdrant
- Sentence Transformers
- Gemini 2.5 Flash
- FastAPI
- Redis (caching)

## 5. Data Ingestion
- Batch + streaming ingestion
- Normalize API responses
- Attach metadata:
```
{
  "source_id": "string",
  "category": "string",
  "timestamp": "datetime",
  "tags": ["string"]
}
```

## 6. Chunking Strategy
- chunk_size: 500
- overlap: 50
- semantic-aware splitting

## 7. Embedding
- Model: BAAI/bge-small-en-v1.5
- Vector size: 384

## 8. Storage (Qdrant)
- Cosine similarity
- HNSW indexing
- Payload indexing for metadata

## 9. Hybrid Retrieval
- Dense Top-K: 50
- BM25 Top-K: 50
- Fusion:
```
score = 0.7 * dense + 0.3 * bm25
```

## 10. Metadata Filtering
Example:
```
{
  "must": [
    {"key": "category", "match": {"value": "finance"}}
  ]
}
```

## 11. Reranking
- Model: cross-encoder/ms-marco-MiniLM-L-6-v2
- Input: Top 20
- Output: Top 5–10

## 12. Context Builder
- Max tokens: ~3000
- Preserve chunk IDs

## 13. LLM Layer
- Gemini 2.5 Flash
- Enforce citations

## 14. Citation System
```
[0] text
[1] text
```

## 15. Performance
- Async ingestion
- Batch embedding
- Redis caching
- HNSW tuning

## 16. Metrics
- Recall@5
- Latency
- Hallucination rate

## 17. Security
- API auth
- Rate limiting

## 18. Future
- Agentic RAG
- Graph RAG
- Query rewriting

