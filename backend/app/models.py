from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import Base
import uuid

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    profile = Column(String(50), nullable=False, default="sop")
    current_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    doc_json = Column(JSONB, nullable=False)
    change_summary = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
