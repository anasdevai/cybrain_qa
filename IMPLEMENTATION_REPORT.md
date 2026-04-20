# Implementation Report: Hybrid RAG Chatbot

This report provides a detailed, step-by-step overview of the architecture, features, and implementation journey of the Hybrid RAG Chatbot (SOPSearch AI).

## 🚀 1. Technology Stack Index

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | FastAPI | High-performance asynchronous API framework |
| **Frontend** | React (Vite) | Modern, fast UI development with HMR |
| **Vector DB** | Qdrant | Storage for dense & sparse vectors with Hybrid Search |
| **Auth DB** | PostgreSQL | Relational storage for users, sessions, and messages |
| **Language Model** | Gemini 2.5 Flash | RAG generation with citations |
| **Embedding Model**| `BGE-Small-en-v1.5` | Dense vector generation for semantic search |
| **Reranker** | `MS-Marco MiniLM` | Cross-encoder for precise context relevancy |
| **ORM** | SQLAlchemy (Async) | Asynchronous database interactions |
| **Migrations** | Alembic | Version control for PostgreSQL schema |
| **Authentication** | JWT + Bcrypt | Secure token-based access & password hashing |
| **Environment** | python-dotenv | Secure secret management |

---

## 🛠️ 2. Detailed Step-by-Step Implementation

### Phase 1: Core Backend & Vector Foundation
1. **Initialize Project:** Set up the directory structure with `main.py`, `routers/`, `database/`, and `retrieval/`.
2. **Qdrant Integration:** Configured Qdrant collection to support **Hybrid Search** (both 384-dim dense vectors and sparse BM25 vectors).
3. **Ingestion Pipeline:** Created scripts to chunk SOP documents and upsert them into Qdrant with metadata (SOP #, Title, etc.).

### Phase 2: Intelligence & RAG Pipeline
1. **Hybrid Retrieval:** Implemented a search layer that queries Qdrant for both semantic (Dense) and keyword (Lexical) matches.
2. **Cross-Encoder Reranking:** Integrated `SentenceTransformers` to rerank the top 10 retrieved chunks, selecting only the most relevant context.
3. **Gemini Chain:** Connected the reranked context to **Gemini 2.5 Flash** using a custom prompt that enforces citation-only responses to prevent hallucinations.

### Phase 3: Security & Relational Database Layer
1. **PostgreSQL Setup:** Configured an asynchronous SQLAlchemy engine to connect to a local PostgreSQL instance.
2. **Schema Design:** Created `users`, `chat_sessions`, and `chat_messages` tables with clear relationships.
3. **JWT Authentication:** 
   - Implemented `register` and `login` endpoints.
   - Built a custom `get_current_user` dependency to protect the `/query` and `/chat_history` routes.
4. **Alembic Migrations:** Initialized and applied migrations to synchronize the database schema.

### Phase 4: Frontend Development
1. **Vite + React Setup:** Scaffolded the frontend with a dark-mode focused design system.
2. **Auth Integration:** 
   - Built a secure Login/SignUp screen.
   - Implemented `localStorage` token management and automatic 401 (Unauthorized) redirect handling.
3. **Chat Interface:** 
   - Created a dynamic sidebar for chat history.
   - Implemented a "threaded" message view with source citations displayed clearly below each AI response.
   - Integrated `react-markdown` for formatted AI output.

### Phase 5: Profile System & Final Polish
1. **Profile Settings Panel:** Built a slide-in drawer allowing users to update their **Username** and **Password** (verified by the current password).
2. **Glassmorphism UI:** Enhanced the interface with backdrop blurs, gradients, and modern micro-animations.
3. **Responsiveness:** Added media queries ensuring the chatbot works perfectly on Mobile, Tablet, and Desktop.
4. **Git Synchronization:** Initialized local Git, configured `.gitignore`, and connected the project to **GitHub** (`anasdevai/Hybrid_Rag`).

---

## 🧠 3. Core Workflow: The Lifecycle of a Query

1. **User Input:** User submits a search query via the React interface.
2. **JWT Verification:** FastAPI validates the Bearer token to ensure the user is authorized.
3. **Hybrid Retrieval:** The query is sent to Qdrant to retrieve the top `K` most relevant chunks across both vector space and keyword matching.
4. **Deep Reranking:** The `MS-MARCO` cross-encoder reranks the retrieved chunks based on their absolute semantic relevance to the query.
5. **Gemini 2.5 Contextual Generation:** The final top-ranked context is passed to the Gemini model to synthesize an answer with source citations.
6. **Persistence:** The query and answer are saved to the PostgreSQL database for chat history retrieval.

---

## ✅ 4. Current Implementation Status

> [!IMPORTANT]
> **Status: Production Ready Layer Established**
> The system is now fully authenticated, persistent, and intelligent.

- [x] **Secure Auth:** Users can register and sign in.
- [x] **Persistent Chat:** History is saved across sessions in PostgreSQL.
- [x] **Hybrid Search:** Searches are fast and accurate.
- [x] **Reranking:** Minimizes noise in AI context.
- [x] **Profile Management:** Users can manage their identity.
- [x] **Source Citations:** AI never answers without proof.

---

## 📁 5. Repository Structure

```text
Hybrid_rag/
├── alembic/            # Database migration history
├── auth/               # Security & JWT logic
├── database/           # Models, Config, and DB utility
├── frontend/           # Vite + React Application
├── ingestion/          # SOP Data processing scripts
├── retrieval/          # Hybrid search & Reranking logic
├── schemas/            # Pydantic models for validation
├── main.py             # FastAPI App entry point
└── requirements.txt    # Backend dependencies
```
