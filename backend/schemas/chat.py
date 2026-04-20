"""Pydantic v2 schemas for chat sessions and history tracking."""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    collection_name: str = os.getenv("COLLECTION_SOPS", "docs_sops")
    category_filter: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    collection_name: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    session_id: UUID
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=50000)
    citations: Optional[List[Dict[str, Any]]] = None
    retrieval_metadata: Optional[Dict[str, Any]] = None
    
    # Audit Vault Snapshots
    metadata_snapshot: Optional[List[Dict[str, Any]]] = None
    audit_log_snapshot: Optional[List[Dict[str, Any]]] = None
    action_metadata: Optional[Dict[str, Any]] = None
    
    category_filter: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: Optional[List[Dict[str, Any]]]
    retrieval_metadata: Optional[Dict[str, Any]]
    
    # Audit Vault Snapshots
    metadata_snapshot: Optional[List[Dict[str, Any]]] = None
    audit_log_snapshot: Optional[List[Dict[str, Any]]] = None
    action_metadata: Optional[Dict[str, Any]] = None
    
    category_filter: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]
    total_messages: int
