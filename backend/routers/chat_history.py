"""Chat history routing endpoints for managing sessions and messages."""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID

from database.config import get_db
from database.models import User, ChatSession, ChatMessage
from schemas.chat import (
    ChatSessionCreate, 
    ChatSessionResponse, 
    ChatMessageCreate, 
    ChatMessageResponse,
    ChatHistoryResponse
)
from auth.security import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat History"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new chat session for the current user."""
    db_session = ChatSession(
        user_id=current_user.id,
        title=session_in.title,
        collection_name=session_in.collection_name,
    )
    
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    return db_session


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all active chat sessions for the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(desc(ChatSession.updated_at))
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific session with all its messages."""
    # Verify session ownership
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.is_active == True)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
        
    # Get messages
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()
    
    return {
        "session": session,
        "messages": messages,
        "total_messages": len(messages)
    }


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: UUID,
    message_in: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Append a message to a session."""
    # Verify session ownership
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.is_active == True))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
        
    # Auto-generate title if this is the first message and it's from the user
    if not session.title and message_in.role == "user":
        # Create a short title from the user query (first 50 chars)
        session.title = message_in.content[:50] + ("..." if len(message_in.content) > 50 else "")
        db.add(session)
        
    db_message = ChatMessage(
        session_id=session_id,
        role=message_in.role,
        content=message_in.content,
        citations=message_in.citations,
        retrieval_metadata=message_in.retrieval_metadata,
        # Audit Vault Snapshots
        metadata_snapshot=message_in.metadata_snapshot,
        audit_log_snapshot=message_in.audit_log_snapshot,
        action_metadata=message_in.action_metadata,
        category_filter=message_in.category_filter
    )
    
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    
    return db_message


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft delete a chat session."""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")
        
    session.is_active = False
    await db.commit()
