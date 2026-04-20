# Legal Counsel AI — Hybrid RAG Chatbot
### Full Technical Documentation

> **Live URL:** `http://65.21.244.158:8085`  
> **Stack:** FastAPI · PostgreSQL · Qdrant · LangChain · Gemini 2.5 Flash · React · Docker Compose  
> **Last Updated:** April 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [System Components](#3-system-components)
4. [Directory Structure](#4-directory-structure)
5. [RAG Pipeline Deep Dive](#5-rag-pipeline-deep-dive)
6. [API Reference](#6-api-reference)
7. [Database Schema](#7-database-schema)
8. [Configuration & Environment Variables](#8-configuration--environment-variables)
9. [Deployment Guide](#9-deployment-guide)
10. [Docker Compose Services](#10-docker-compose-services)
11. [CI/CD & Scripts](#11-cicd--scripts)
12. [Security Notes](#12-security-notes)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Project Overview

**Legal Counsel AI** is an intelligent document retrieval and Q&A system ("Firm Intelligence Node") built for legal and regulatory compliance teams. It allows authenticated users to query a corpus of legal documents across five structured collections using natural language.

### Key Features

| Feature | Description |
|---|---|
| **Hybrid Search** | Combines dense vector search (BAAI/bge-small-en-v1.5) + sparse BM25 keyword search (70/30 weighted fusion) |
| **Smart Query Routing** | Keyword-based intent detection routes queries to only the relevant collection(s), reducing latency and noise |
| **Cross-Encoder Reranking** | `cross-encoder/ms-marco-MiniLM-L-6-v2` re-scores retrieved candidates for precision |
| **5-Collection Federated Search** | SOPs, Deviations, CAPAs, Audits, Decisions — searched in parallel |
| **Audit Vault** | Every query logs metadata snapshots and audit trails alongside chat history |
| **JWT Authentication** | Secure user registration, login, token refresh, and profile management |
| **Real-time Webhooks** | External systems can push document changes to Qdrant via webhook endpoints |

---

## 2. Architecture Diagram

![System Architecture Diagram](file:///C:/Users/ce/.gemini/antigravity/brain/d779e95a-e9bb-4a40-bfd0-7eab1761f44f/hybrid_rag_architecture_diagram_1775908477577.png)

### 2.1 Technical Flow Overview

---

## 3. System Components

### 3.1 Frontend — React SPA

| Item | Detail |
|---|---|
| **Framework** | React 18 + Vite |
| **Styling** | Inline CSS (dark theme, glassmorphism) |
| **API Base** | `/api` (proxied through Nginx) |
| **Auth Storage** | `localStorage` (JWT access token + refresh) |
| **Key Pages** | Login / Register, Chat Interface, Profile |
| **Build Output** | `frontend/dist/` (served as static files by Nginx) |

### 3.2 Backend — FastAPI

| Item | Detail |
|---|---|
| **Framework** | FastAPI 0.11+ with async SQLAlchemy |
| **Server** | Uvicorn (1 worker — HuggingFace model constraint) |
| **Auth** | JWT via `python-jose`, bcrypt passwords via `passlib` |
| **DB Driver** | `asyncpg` over PostgreSQL |
| **Migration** | Alembic (2 versions: initial schema + audit vault fields) |

### 3.3 Vector Database — Qdrant Cloud

Five named collections, each holding chunked legal documents with metadata:

| Collection | Key | Purpose |
|---|---|---|
| `docs_sops` | `sops` | Standard Operating Procedures |
| `docs_deviations` | `deviations` | Incidents & Violations |
| `docs_capas` | `capas` | Corrective & Preventive Actions |
| `docs_audits` | `audits` | Audit Findings |
| `docs_decisions` | `decisions` | Management Decisions |

### 3.4 LLM — Google Gemini API

- **Model:** `gemini-2.5-flash`
- **Temperature:** `0.2` (low hallucination)
- **Max Tokens:** `2048`
- **Max Retries:** `6`
- **Thinking Budget:** `0` (disabled for speed)

---

## 4. Directory Structure

```
Main/
├── main.py                    # FastAPI app entry point, startup event, endpoints
├── Dockerfile                 # Backend container build
├── docker-compose.yml         # Service orchestration (hybridrag project)
├── nginx/
│   └── nginx.conf             # Nginx reverse proxy config (port 8085 → :80 → :8000)
├── frontend/
│   ├── src/App.jsx            # Single-page React application
│   ├── vite.config.js
│   └── dist/                  # Built static files (served by Nginx)
├── alembic/
│   ├── env.py                 # Alembic migration environment
│   └── versions/
│       ├── 0001_initial_schema.py    # users, chat_sessions, chat_messages
│       └── 0002_add_audit_vault_fields.py  # metadata_snapshot, audit_log_snapshot, action_metadata
├── auth/
│   └── security.py            # JWT encode/decode, password hashing, get_current_user
├── database/
│   ├── config.py              # Async SQLAlchemy engine + session factory
│   └── models.py              # ORM models: User, ChatSession, ChatMessage
├── schemas/                   # Pydantic request/response models
├── routers/
│   ├── auth.py                # /auth/register, /auth/login, /auth/me, /auth/refresh
│   ├── chat_history.py        # /chat/sessions, /chat/sessions/{id}/messages
│   └── webhooks.py            # /webhook/* — Qdrant document sync endpoints
├── embeddings/
│   └── embedder.py            # HuggingFace BAAI/bge-small-en-v1.5 embedder
├── retrieval/
│   ├── query_router.py        # Keyword-based intent routing → collection selection
│   ├── hybrid_retriever.py    # Dense (Qdrant) + BM25 fusion retriever
│   ├── reranker.py            # Cross-encoder reranker (ms-marco-MiniLM-L-6-v2)
│   ├── federated_retriever.py # Parallel retrieval across multiple collections
│   └── context_builder.py    # Formats retrieved docs into LLM context string
├── chain/
│   └── rag_chain.py           # HybridRAGChain + SmartRAGChain (routing + generation)
├── ingestion/                 # Document chunking and upload utilities
├── storage/                   # File storage helpers
├── scripts/
│   ├── _ssh_deploy.py         # Manual SCP-based deployment script
│   ├── force_fix_db.py        # Emergency SQL schema fix utility
│   ├── stamp_alembic.py       # Alembic version stamping utility
│   └── fetch_detailed_logs.py # Remote log fetcher
├── requirements.txt           # AI/API dependencies
├── requirements.db.txt        # Database dependencies
├── .env                       # Environment variables (NOT committed)
└── .env.example               # Template for environment setup
```

---

## 5. RAG Pipeline Deep Dive

### Step 1: Query Routing

```
User Query → query_router.py
```

The `route_query()` function uses regex keyword matching to determine which of the 5 Qdrant collections to search:

- **Specific match** → searches 1 collection (e.g., `"Show me the SOP for access control"` → `["sops"]`)
- **Multi-match** → searches top 2 collections by keyword score
- **Broad/ambiguous** → searches ALL 5 collections (triggered by words like `"all"`, `"related"`, `"show me"`)

### Step 2: Hybrid Retrieval

```
Query + Collection List → HybridRetriever (per collection)
```

For each targeted collection, the `HybridRetriever` performs:

1. **Dense Search**: Queries Qdrant with the embedded query vector (`BAAI/bge-small-en-v1.5`)
   - Returns top 50 results by cosine similarity
2. **BM25 Sparse Search**: Scrolls the full collection (cached for 5 minutes), tokenizes, scores with `rank_bm25`
   - Returns top 50 results by BM25 Okapi scoring
3. **Score Fusion**: Normalizes both score arrays to [0, 1], then fuses:
   - `final_score = 0.7 × dense_score + 0.3 × bm25_score`
4. Returns top 20 fused documents

### Step 3: Cross-Encoder Reranking

```
Fused Docs → CrossEncoderReranker → Top-N Docs
```

The `cross-encoder/ms-marco-MiniLM-L-6-v2` model re-scores each (query, document) pair. This is a more expensive but accurate "reading comprehension" style score that catches semantic matches missed by embedding similarity.

- Single collection: `top_n = 5`
- Multiple collections: `top_n = 3` per collection

### Step 4: Context Building

```
Reranked Docs → context_builder.py → Numbered Context String
```

Documents are formatted with headers: `[0] SOP "Title" (Active)\n{text}`, capped at 14,000 characters total.

### Step 5: LLM Generation

```
Context + Query → Gemini 2.5 Flash → Structured Response
```

The system prompt enforces a strict output format:
- **Direct Answer** (2–4 sentences)
- **Key Points** (bullet list with document IDs)
- **Summary** (with risk level emoji for risk queries)
- **Sources** table
- `---CITATIONS---` JSON block (parsed by code)
- `---SUGGESTIONS---` JSON array (parsed by code)

### Step 6: Response Assembly

The backend parses the LLM output, merges citations with retrieval metadata, and returns a `SmartQueryResponse` containing:
- `answer` — clean prose
- `citations` — enriched with ref numbers, types, status
- `suggestions` — 3–4 follow-up queries
- `retrieval_stats` — latency, collections searched, doc counts
- `metadata_snapshot` + `audit_log_snapshot` — Audit Vault data

---

## 6. API Reference

### Authentication

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/auth/register` | `{email, username, password}` | Create new user account |
| `POST` | `/auth/login` | `{email, password}` | Returns JWT access + refresh tokens |
| `GET` | `/auth/me` | — | Get current user profile (Bearer token required) |
| `PATCH` | `/auth/me` | `{username?, email?}` | Update profile |
| `POST` | `/auth/refresh` | `{refresh_token}` | Rotate access token |

### Chat Sessions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/chat/sessions` | List user's chat sessions |
| `POST` | `/chat/sessions` | Create new session |
| `GET` | `/chat/sessions/{id}` | Get session with all messages |
| `DELETE` | `/chat/sessions/{id}` | Delete session |
| `POST` | `/chat/sessions/{id}/messages` | Append a message to session |

### Query

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/query/federated` | `{query, category?}` | Smart multi-collection RAG query |
| `POST` | `/query/smart` | `{query, category?}` | Alias for `/query/federated` |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok"}` |

### Webhooks

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/webhooks/qdrant/sync` | Primary generic sync endpoint (`create/update/delete` via payload) |
| `PUT` | `/webhooks/qdrant/sync` | Idempotent update endpoint (forces `update`) |
| `POST` | `/webhook/{entity}` | Legacy compatibility upsert route (`sops`, `deviations`, `capas`, `audits`, `decisions`) |
| `PUT` | `/webhook/{entity}/{id}` | Legacy compatibility update route |
| `DELETE` | `/webhook/{entity}/{id}` | Legacy compatibility delete route |

> All routes except `/health` require `Authorization: Bearer <token>` header.  
> Webhook routes additionally verify `x-webhook-secret` header.

---

## 7. Database Schema

### `users` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, auto-generated |
| `email` | VARCHAR(255) | Unique, indexed |
| `username` | VARCHAR(100) | Unique, indexed |
| `hashed_password` | VARCHAR(255) | bcrypt |
| `is_active` | BOOLEAN | Default `true` |
| `is_verified` | BOOLEAN | Default `false` |
| `role` | ENUM(`admin`, `user`) | Default `user` |
| `created_at` | TIMESTAMPTZ | Auto now |
| `updated_at` | TIMESTAMPTZ | Auto on update |
| `last_login` | TIMESTAMPTZ | Nullable |

### `chat_sessions` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `users.id` (CASCADE DELETE) |
| `title` | VARCHAR(500) | Nullable |
| `collection_name` | VARCHAR(255) | Active collection context |
| `created_at` | TIMESTAMPTZ | Auto now |
| `updated_at` | TIMESTAMPTZ | Auto on update |
| `is_active` | BOOLEAN | Default `true` |

### `chat_messages` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | FK → `chat_sessions.id` (CASCADE DELETE) |
| `role` | ENUM(`user`, `assistant`) | Message speaker |
| `content` | TEXT | Message text |
| `citations` | JSON | Retrieved document references |
| `retrieval_metadata` | JSON | Stats about the retrieval |
| `metadata_snapshot` | JSON | ⭐ Audit Vault: full document metadata |
| `audit_log_snapshot` | JSON | ⭐ Audit Vault: audit trail entries |
| `action_metadata` | JSON | ⭐ Audit Vault: query routing + latency |
| `category_filter` | VARCHAR(100) | Optional category override |
| `created_at` | TIMESTAMPTZ | Auto now |

> ⭐ Columns added in Alembic migration `0002`

### Alembic Migrations

| Version | Description |
|---|---|
| `0001` | Initial schema: users, chat_sessions, chat_messages |
| `0002` | Added Audit Vault fields to chat_messages |

---

## 8. Configuration & Environment Variables

Create a `.env` file in the project root:

```dotenv
# === General ===
API_BASE_URL=http://65.21.244.158
API_KEY=dummy_developer_key

# === Google AI (Gemini) ===
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# === Qdrant Cloud ===
QDRANT_URL=https://<your-cluster>.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key-here

# === Qdrant Collection Names ===
COLLECTION_NAME=hybrid_rag_docs            # Legacy (not used)
COLLECTION_SOPS=docs_sops
COLLECTION_DEVIATIONS=docs_deviations
COLLECTION_CAPAS=docs_capas
COLLECTION_DECISIONS=docs_decisions
COLLECTION_AUDITS=docs_audits

# === PostgreSQL (Docker service name as host) ===
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password-here
POSTGRES_HOST=db                           # ← Must be 'db' in Docker, 'localhost' for local dev
POSTGRES_PORT=5432
POSTGRES_DB=qdrant

# === JWT Authentication ===
JWT_SECRET_KEY=your-256-bit-secret-here
JWT_REFRESH_SECRET_KEY=your-refresh-secret-here

# === Webhook Security ===
WEBHOOK_SECRET=your-webhook-secret-here

# === Runtime Endpoint Auto-Sync ===
ENABLE_ENDPOINT_AUTO_SYNC=true
ENDPOINT_SYNC_INTERVAL_SECONDS=60
```

> **Important:** `POSTGRES_HOST=db` when running inside Docker Compose. Change to `localhost` for local development only.

---

## 9. Deployment Guide

### Prerequisites

- Docker + Docker Compose v2
- Python 3.11+ (for local scripts)
- Server with at least 4GB RAM + 2GB swap

### Initial Server Setup

```bash
# SSH into server
ssh root@65.21.244.158

# Create isolated deployment directory
mkdir -p /opt/hybrid-rag-isolated
cd /opt/hybrid-rag-isolated

# Upload project files (from local machine)
python scripts/_ssh_deploy.py

# Create .env file
nano .env  # Add all variables from Section 8

# Set up swap memory (required for 4GB servers)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Build and Start

```bash
cd /opt/hybrid-rag-isolated

# First time: full build
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

### Update Deployment (Code Changes)

```bash
# From local machine: upload changed files
python scripts/_ssh_deploy.py

# On server: rebuild backend (uses cached layers)
cd /opt/hybrid-rag-isolated
docker compose build backend
docker compose up -d
```

### Rolling Restart (Config/Env Changes Only)

```bash
cd /opt/hybrid-rag-isolated
docker compose restart backend
```

---

## 10. Docker Compose Services

> Located at: `docker-compose.yml` | Project name: `hybridrag`

```yaml
services:
  nginx:    # Serves static frontend + proxies /api/* to backend
            # External port: 8085 → internal port: 80
  
  backend:  # FastAPI + Uvicorn
            # Internal port: 8000 (not exposed externally)
            # Memory limit: 2GB
            # Health check: GET /health every 30s (5 retries, 90s start delay)
  
  db:       # PostgreSQL 16 Alpine
            # Internal port: 5432 (not exposed externally)
            # Memory limit: 256MB
            # Data volume: ./data/postgres
```

### Container Names

| Service | Container Name |
|---|---|
| nginx | `hybridrag-nginx-1` |
| backend | `hybridrag-backend-1` |
| db | `hybridrag-db-1` |

### Startup Order

```
db (healthy) → backend (healthy) → nginx (starts)
```

---

## 11. CI/CD & Scripts

### `scripts/_ssh_deploy.py`
Manual deployment script. Tarballs the project locally, transfers via SCP, extracts on the server, and runs `docker compose up -d`.

```bash
python scripts/_ssh_deploy.py
```

### `scripts/force_fix_db.py`
Emergency script to directly apply SQL `ALTER TABLE` commands if Alembic migrations fail. Also uploads the `.env` file.

```bash
python scripts/force_fix_db.py
```

### `scripts/stamp_alembic.py`
Updates the `alembic_version` table directly when migrations are stuck due to schema already being applied manually.

```bash
python scripts/stamp_alembic.py
```

### `deploy.sh`
Shell script run on the server that skips `git pull` (code is uploaded via SCP) and runs `docker compose build + up`.

### `.github/workflows/deploy.yml`
GitHub Actions CI workflow that SSHs into the server and triggers `deploy.sh` on push to `main` branch.

---

## 12. Security Notes

> [!CAUTION]
> The following credentials were used during development. **Change them before using in production.**

- **Server root password** should be rotated or replaced with SSH key authentication
- **JWT secrets** should be 256-bit random values — use `openssl rand -hex 32`
- **`API_KEY`** (`dummy_developer_key`) is a placeholder; implement proper API key validation
- **CORS** is currently restricted to `localhost:5173/5174` — update for production domains
- **Webhook secret** should be a strong random value shared only with trusted systems
- **`.env` file** must never be committed to git (it is listed in `.gitignore`)

### Recommended Security Improvements

1. Add SSH key to server: `ssh-copy-id root@65.21.244.158`
2. Disable root password login: `PasswordAuthentication no` in `/etc/ssh/sshd_config`
3. Enable UFW firewall: `ufw allow 8085 && ufw allow 22 && ufw enable`
4. Add HTTPS via Let's Encrypt + Nginx SSL termination
5. Update CORS `allow_origin_regex` to your actual frontend domain

---

## 13. Troubleshooting

### Backend crash-looping on startup

**Symptom:** `docker compose ps` shows `Restarting`
**Cause:** Most commonly a database connection error or migration failure.

```bash
# Check what's happening
docker compose logs backend --tail 50

# Common fixes:
# 1. Verify POSTGRES_HOST=db (not localhost) in .env
# 2. Make sure DB is healthy before backend starts
docker compose restart db
docker compose up -d backend
```

### `Server error 500` in the UI

**Symptom:** Chat queries return 500, but /health is OK
**Cause:** Database schema mismatch (columns missing from `chat_messages`)

```bash
# Check the actual error
docker compose logs backend --tail 30

# Fix if columns are missing:
docker compose exec -T db psql -U postgres -d qdrant \
  -c "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS metadata_snapshot JSON;"
docker compose exec -T db psql -U postgres -d qdrant \
  -c "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS audit_log_snapshot JSON;"
docker compose exec -T db psql -U postgres -d qdrant \
  -c "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS action_metadata JSON;"

# Then stamp alembic and restart
docker compose exec -T db psql -U postgres -d qdrant \
  -c "UPDATE alembic_version SET version_num='0002' WHERE version_num='0001';"
docker compose restart backend
```

### `Failed to fetch` on login/register

**Symptom:** Network error in browser console
**Cause:** Frontend API_URL pointing to wrong host, or Nginx not running

```bash
# Check if nginx is up
docker compose ps nginx

# Start nginx if missing
docker compose up -d nginx

# Verify API_URL in frontend (should be '/api', not 'http://...:8000')
grep "API_URL" frontend/src/App.jsx
```

### Server SSH unresponsive (OOM)

**Symptom:** SSH connection times out
**Cause:** Backend OOM-killed during HuggingFace model loading

**Fix:** Hard reboot from hosting provider dashboard, then:
```bash
# After reboot — set up swap to prevent repeat
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab  # Make permanent
```

### Alembic migration fails on `docker compose up`

**Symptom:** `DuplicateColumnError` in backend logs during alembic upgrade

**Cause:** Columns were manually added but `alembic_version` still tracks an old version.

```bash
# Stamp the version to reflect reality
docker compose exec -T db psql -U postgres -d qdrant \
  -c "UPDATE alembic_version SET version_num='0002';"
docker compose restart backend
```

---

*Generated from the deployed production system — April 2026*
