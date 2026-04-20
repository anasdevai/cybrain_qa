"""SQLAlchemy ORM models representing the PostgreSQL schema."""

import uuid
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(Enum("admin", "user", name="user_roles"), default="user", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    ai_suggestions = relationship("AISuggestion", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    collection_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum("user", "assistant", name="message_roles"), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    retrieval_metadata = Column(JSON, nullable=True)
    
    # Audit Vault Fields
    metadata_snapshot = Column(JSON, nullable=True)
    audit_log_snapshot = Column(JSON, nullable=True)
    action_metadata = Column(JSON, nullable=True)
    
    category_filter = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}')>"


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(255), nullable=False, index=True)
    section_id = Column(String(255), nullable=False, index=True)
    section_title = Column(String(255), nullable=True)
    section_type = Column(String(100), nullable=True)
    action_type = Column(String(50), nullable=False, index=True)
    input_text = Column(Text, nullable=True)
    output_text = Column(JSONB, nullable=False)
    related_documents = Column(JSONB, nullable=True)
    metadata_snapshot = Column(JSONB, nullable=True)
    audit_log_snapshot = Column(JSONB, nullable=True)
    action_metadata = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="ai_suggestions")

    def __repr__(self):
        return (
            f"<AISuggestion(id={self.id}, action_type='{self.action_type}', "
            f"document_id='{self.document_id}', section_id='{self.section_id}')>"
        )
