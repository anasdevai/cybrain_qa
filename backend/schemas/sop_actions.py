"""Pydantic schemas for SOP editor action endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_SECTION_TYPES = {
    "Procedure",
    "Scope",
    "Purpose",
    "Responsibilities",
    "Documentation",
    "Full Document",
}

VALID_CHANGE_CATEGORIES = {
    "clarity_improvement",
    "compliance_alignment",
    "error_correction",
    "process_update",
    "regulatory_requirement",
}


class ActionRequest(BaseModel):
    section_text: str = Field(..., min_length=1)
    sop_title: str = Field(..., min_length=1)
    section_title: str = Field(..., min_length=1)
    section_type: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)

    @field_validator("section_type")
    @classmethod
    def normalize_section_type(cls, value: str) -> str:
        normalized = value.strip()
        if normalized in VALID_SECTION_TYPES:
            return normalized
        return normalized


class JustifyRequest(ActionRequest):
    old_text: str = Field(..., min_length=1)
    new_text: str = Field(..., min_length=1)
    change_type: str = Field(..., min_length=1)


class ImproveResponse(BaseModel):
    improved_text: str
    changes_made: list[str]
    compliance_note: str


class RewriteResponse(BaseModel):
    rewritten_text: str
    structural_changes: list[str]
    rationale: str


class GapItem(BaseModel):
    issue: str
    explanation: str
    recommendation: str


class GapCheckResponse(BaseModel):
    gaps: list[GapItem]
    section_assessed: str


class ConvertResponse(BaseModel):
    purpose: str
    scope: str
    responsibilities: str
    procedure: list[str]
    documentation: str


class JustifyResponse(BaseModel):
    justification: str
    change_category: str
    regulatory_reference: str | None = None

    @field_validator("change_category")
    @classmethod
    def validate_change_category(cls, value: str) -> str:
        if value not in VALID_CHANGE_CATEGORIES:
            raise ValueError("invalid change category")
        return value


class ActionResponseEnvelope(BaseModel):
    suggestion_id: int
    result: Any
    related_documents: list[str]
    action_type: str
    status: str = "pending"


class SuggestionStatusUpdate(BaseModel):
    status: Literal["accepted", "rejected"]


class SuggestionStatusResponse(BaseModel):
    id: int
    status: str
    updated_at: datetime | None = None


class AISuggestionResponse(BaseModel):
    id: int
    document_id: str
    section_id: str
    section_title: str | None = None
    section_type: str | None = None
    action_type: str
    output_text: dict[str, Any]
    related_documents: list[str] | None = None
    metadata_snapshot: dict[str, Any] | None = None
    audit_log_snapshot: list[dict[str, Any]] | None = None
    action_metadata: dict[str, Any] | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
