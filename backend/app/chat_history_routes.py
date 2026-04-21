from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth_routes import get_current_user
from .database import get_db
from .models import ChatMessage, ChatSession, User


router = APIRouter(prefix="/api/chat", tags=["Chat History"])


class CreateSessionRequest(BaseModel):
    title: str | None = None
    collection_name: str = "docs_sops"


class AddMessageRequest(BaseModel):
    role: str
    content: str
    citations: dict | list | None = None
    retrieval_metadata: dict | None = None
    metadata_snapshot: dict | list | None = None
    audit_log_snapshot: dict | list | None = None
    action_metadata: dict | None = None
    category_filter: str | None = None


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "collection_name": s.collection_name,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "is_active": s.is_active,
        }
        for s in sessions
    ]


@router.post("/sessions")
def create_session(
    payload: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(
        user_id=current_user.id,
        title=payload.title,
        collection_name=payload.collection_name or "docs_sops",
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "id": str(session.id),
        "title": session.title,
        "collection_name": session.collection_name,
        "created_at": session.created_at,
    }


@router.get("/sessions/{session_id}/messages")
def list_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(m.id),
            "session_id": str(m.session_id),
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "retrieval_metadata": m.retrieval_metadata,
            "metadata_snapshot": m.metadata_snapshot,
            "audit_log_snapshot": m.audit_log_snapshot,
            "action_metadata": m.action_metadata,
            "category_filter": m.category_filter,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.post("/sessions/{session_id}/messages")
def add_message(
    session_id: UUID,
    payload: AddMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (payload.role or "").strip().lower()
    if role not in {"user", "assistant"}:
        raise HTTPException(status_code=422, detail="role must be 'user' or 'assistant'")
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=422, detail="content is required")

    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    message = ChatMessage(
        session_id=session.id,
        role=role,
        content=payload.content.strip(),
        citations=payload.citations,
        retrieval_metadata=payload.retrieval_metadata,
        metadata_snapshot=payload.metadata_snapshot,
        audit_log_snapshot=payload.audit_log_snapshot,
        action_metadata=payload.action_metadata,
        category_filter=payload.category_filter,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "id": str(message.id),
        "session_id": str(message.session_id),
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
    }
