import sys
import io
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))
sys.path.append(os.path.join(PROJECT_ROOT, "chatbot"))
sys.path.append(os.path.join(PROJECT_ROOT, "database"))
sys.path.append(PROJECT_ROOT)

# Robust fix for transformers crash in headless environments (AttributeError: 'NoneType' object has no attribute 'isatty')
# This must happen before ANY other imports (especially langchain/transformers)
# if sys.stdout is None or not hasattr(sys.stdout, 'isatty'):
#     sys.stdout = io.StringIO()
# if sys.stderr is None or not hasattr(sys.stderr, 'isatty'):
#     sys.stderr = io.StringIO()

import asyncio

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from uuid import UUID
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from embeddings.embedder import get_embedder
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import CrossEncoderReranker
from retrieval.federated_retriever import FederatedRetriever
from chain.rag_chain import HybridRAGChain, SmartRAGChain
from routers import auth, chat_history, webhooks, data
from storage.runtime_sync import RuntimeEndpointSync
from auth.security import get_current_user
from database.models import User, ChatSession, ChatMessage
from database.config import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from dotenv import load_dotenv
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

load_dotenv()

app = FastAPI(title="Hybrid RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[34]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat_history.router)
app.include_router(webhooks.router)
app.include_router(webhooks.legacy_router)
app.include_router(data.router)
app.state.runtime_sync_task = None


@app.on_event("startup")
async def startup():
    qdrant_url     = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    client   = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    embedder = get_embedder()

    # Legacy single-collection chain has been removed as the hybrid_rag_docs collection was deleted by user request.

    # ── Smart multi-collection chain ──
    reranker = CrossEncoderReranker(top_n=5)
    
    collection_map = {
        "sops":       os.getenv("COLLECTION_SOPS",       "docs_sops"),
        "deviations": os.getenv("COLLECTION_DEVIATIONS", "docs_deviations"),
        "capas":      os.getenv("COLLECTION_CAPAS",      "docs_capas"),
        "audits":     os.getenv("COLLECTION_AUDITS",     "docs_audits"),
        "decisions":  os.getenv("COLLECTION_DECISIONS",  "docs_decisions"),
    }

    vectorstores = {
        section: QdrantVectorStore(client=client, collection_name=col, embedding=embedder)
        for section, col in collection_map.items()
    }

    federated_retriever = FederatedRetriever(client=client, vectorstores=vectorstores, reranker=reranker)
    for section, col in collection_map.items():
        federated_retriever.retrievers[section].collection_name = col

    app.state.smart_rag = SmartRAGChain(federated_retriever)
    print("[startup] Smart RAG chain ready (5 collections with query routing).")

    runtime_sync = RuntimeEndpointSync()
    if runtime_sync.enabled:
        app.state.runtime_sync_task = asyncio.create_task(runtime_sync.run_forever())
        print("[startup] Runtime endpoint auto-sync started.")
    else:
        print("[startup] Runtime endpoint auto-sync disabled.")


@app.on_event("shutdown")
async def shutdown():
    task = getattr(app.state, "runtime_sync_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# --------------------------------------------------------------------------
# Request / Response schemas
# --------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    category: Optional[str] = None
    session_id: Optional[UUID] = None   # pass this to enable memory / chat continuity


class SmartQueryResponse(BaseModel):
    answer: str
    reasoning: Optional[str] = ""
    confidence: Optional[str] = ""
    citations: List[Dict[str, Any]]
    suggestions: List[str] = []
    retrieval_stats: Dict[str, Any]
    routed_to: str = ""
    cached: bool = False
    
    # Audit Vault Fields
    metadata_snapshot: Optional[List[Dict[str, Any]]] = []
    audit_log_snapshot: Optional[List[Dict[str, Any]]] = []
    action_metadata: Optional[Dict[str, Any]] = {}


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@app.post("/query/smart", response_model=SmartQueryResponse)
async def smart_query_endpoint(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Smart multi-collection query with automatic routing, CoT reasoning,
    and multi-turn memory via session_id.
    - Pass session_id to enable chat history injection into the LLM prompt.
    - User + assistant messages are auto-saved to the session after each turn.
    """
    if not req.query.strip():
        raise HTTPException(400, "Empty query")

    # ── Load chat history from DB if session_id provided ──
    chat_history: List[Dict] = []
    session = None
    if req.session_id:
        sess_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == req.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.is_active == True,
            )
        )
        session = sess_result.scalar_one_or_none()
        
        # FIX: Auto-create session if requested session_id is not found
        if not session:
            session = ChatSession(
                id=req.session_id,
                user_id=current_user.id,
                title=req.query[:50] + ("..." if len(req.query) > 50 else ""),
                collection_name="docs_sops"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        else:
            msg_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == req.session_id)
                .order_by(ChatMessage.created_at)
            )
            messages = msg_result.scalars().all()
            # Keep last 10 turns (20 messages) to stay within token budget
            chat_history = [
                {"role": m.role, "content": m.content}
                for m in messages[-20:]
            ]

    try:
        result = app.state.smart_rag.invoke(
            req.query,
            category=req.category,
            chat_history=chat_history,
        )
    except Exception as e:
        import traceback
        traceback.print_exc() # Print full stack trace to stderr
        logging.exception("Smart query failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="AI provider is temporarily unavailable. Please retry in a few moments.",
        )

    # ── Auto-save user + assistant messages to session ──
    if session:
        user_msg = ChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.query,
            category_filter=req.category,
        )
        db.add(user_msg)

        assistant_msg = ChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=result["answer"],
            citations=result.get("citations"),
            retrieval_metadata=result.get("retrieval_stats"),
            metadata_snapshot=result.get("metadata_snapshot", []),
            audit_log_snapshot=result.get("audit_log_snapshot", []),
            action_metadata=result.get("action_metadata", {}),
            category_filter=req.category,
        )
        db.add(assistant_msg)

        # Auto-title session on first message
        if not session.title and req.query:
            session.title = req.query[:50] + ("..." if len(req.query) > 50 else "")
            db.add(session)

        await db.commit()

    return SmartQueryResponse(
        answer          = result["answer"],
        reasoning       = result.get("reasoning", ""),
        confidence      = result.get("confidence", ""),
        citations       = result["citations"],
        suggestions     = result.get("suggestions", []),
        retrieval_stats = result["retrieval_stats"],
        routed_to       = result.get("routed_to", ""),
        cached          = result.get("cached", False),
        metadata_snapshot  = result.get("metadata_snapshot", []),
        audit_log_snapshot = result.get("audit_log_snapshot", []),
        action_metadata    = result.get("action_metadata", {}),
    )


# Keep /query/federated as alias for backward compat
@app.post("/query/federated", response_model=SmartQueryResponse)
async def federated_query_endpoint(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Federated query endpoint (alias) now with full session and memory support.
    """
    if not req.query.strip():
        raise HTTPException(400, "Empty query")

    # ── Load chat history from DB if session_id provided ──
    chat_history: List[Dict] = []
    session = None
    if req.session_id:
        sess_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == req.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.is_active == True,
            )
        )
        session = sess_result.scalar_one_or_none()
        
        # Auto-create session if requested session_id is not found
        if not session:
            session = ChatSession(
                id=req.session_id,
                user_id=current_user.id,
                title=req.query[:50] + ("..." if len(req.query) > 50 else ""),
                collection_name="docs_sops"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        else:
            msg_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == req.session_id)
                .order_by(ChatMessage.created_at)
            )
            messages = msg_result.scalars().all()
            chat_history = [
                {"role": m.role, "content": m.content}
                for m in messages[-20:]
            ]

    try:
        result = app.state.smart_rag.invoke(
            req.query, 
            category=req.category,
            chat_history=chat_history
        )
    except Exception as e:
        logging.exception("Federated query failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="AI provider is temporarily unavailable. Please retry in a few moments.",
        )

    # ── Auto-save user + assistant messages to session ──
    if session:
        user_msg = ChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.query,
            category_filter=req.category,
        )
        db.add(user_msg)

        assistant_msg = ChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=result["answer"],
            citations=result.get("citations"),
            retrieval_metadata=result.get("retrieval_stats"),
            metadata_snapshot=result.get("metadata_snapshot", []),
            audit_log_snapshot=result.get("audit_log_snapshot", []),
            action_metadata=result.get("action_metadata", {}),
            category_filter=req.category,
        )
        db.add(assistant_msg)
        await db.commit()

    return SmartQueryResponse(
        answer          = result["answer"],
        citations       = result["citations"],
        suggestions     = result.get("suggestions", []),
        retrieval_stats = result["retrieval_stats"],
        routed_to       = result.get("routed_to", ""),
        cached          = result.get("cached", False),
        metadata_snapshot  = result.get("metadata_snapshot", []),
        audit_log_snapshot = result.get("audit_log_snapshot", []),
        action_metadata    = result.get("action_metadata", {}),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
