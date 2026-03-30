from pydantic import BaseModel
from typing import Any, Optional, List
from uuid import UUID
from datetime import datetime

class CreateDocumentRequest(BaseModel):
    title: str
    profile: str = "sop"


class UpdateDocumentRequest(BaseModel):
    doc_json: Any
    metadata_json: Optional[Any] = None


class CreateVersionRequest(BaseModel):
    doc_json: Any
    change_summary: Optional[str] = None
    metadata_json: Optional[Any] = None


class UpdateVersionStatusRequest(BaseModel):
    status: str
    metadata_json: Optional[Any] = None


class VersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    doc_json: Any
    change_summary: Optional[str]
    status: str
    metadata_json: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True
