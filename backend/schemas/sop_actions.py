"""Pydantic schemas for SOP editor action endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, field_validator

VALID_SECTION_TYPES = {
    "Heading",
    "Paragraph",
    "List",
    "Table",
    "Note",
    "Selected Text",
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
    document_id: str = "editor-document"
    section_id: str = "selected-text"
    sop_title: str = "Untitled SOP"
    section_title: str = "Selected text"
    section_type: str = "Selected Text"
    section_text: str

    @field_validator("section_type", mode="before")
    @classmethod
    def normalize_section_type(cls, value: str | None) -> str:
        normalized = (value or "Selected Text").strip().title()
        if normalized in VALID_SECTION_TYPES:
            return normalized
        if normalized.startswith("Heading"):
            return "Heading"
        return "Selected Text"


class JustifyRequest(ActionRequest):
    old_text: str
    new_text: str
    change_type: str


# Simplified: only the improved text is returned
class ImproveResponse(BaseModel):
    improved_text: str


# Simplified: only the rewritten text is returned
class RewriteResponse(BaseModel):
    rewritten_text: str


# Simplified: a single readable analysis string
class GapCheckResponse(BaseModel):
    analysis: str


class ConvertResponse(BaseModel):
    purpose: str
    scope: str
    responsibilities: str
    procedure: list[str]
    documentation: str


class JustifyResponse(BaseModel):
    justification: str
    change_category: Literal[
        "clarity_improvement",
        "compliance_alignment",
        "error_correction",
        "process_update",
        "regulatory_requirement",
    ]
    regulatory_reference: str | None = None


class ActionResponseEnvelope(BaseModel):
    suggestion_id: int | None = None
    result: dict[str, Any]
    related_documents: list[str] = []
    action_type: str
    status: str = "pending"


class SuggestionStatusResponse(BaseModel):
    suggestion_id: int
    status: str


class SuggestionStatusUpdate(BaseModel):
    status: str
