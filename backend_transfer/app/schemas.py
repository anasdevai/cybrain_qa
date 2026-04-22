from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================
# EDITOR COMPATIBILITY LAYER — REQUEST BODIES
# ==========================================

class CreateDocumentRequest(BaseModel):
    title: Optional[str] = None
    profile: str = "sop"
    doc_json: Optional[Any] = None
    metadata_json: Optional[Any] = None

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


# ==========================================
# EDITOR COMPATIBILITY LAYER — RESPONSES
# These use old editor field names (doc_json, doc_id, status)
# Mapping: doc_json = content_json, status = external_status, doc_id = sop_id
# ==========================================

class EditorVersionResponse(BaseModel):
    """
    Old editor version response shape.
    doc_json   <- sop_versions.content_json
    doc_id     <- sop_versions.sop_id
    status     <- sop_versions.external_status
    """
    id: UUID
    doc_id: UUID                    # maps from sop_versions.sop_id
    version_number: str
    status: str                     # maps from sop_versions.external_status
    doc_json: Optional[Any]         # maps from sop_versions.content_json
    metadata_json: Optional[Any]
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EditorDocResponse(BaseModel):
    """
    Old editor top-level doc response shape.
    doc_json   <- sop_versions.content_json (from current version)
    status     <- sop_versions.external_status
    """
    id: UUID                        # sops.id
    title: Optional[str] = None
    doc_type: str = "sop"
    doc_json: Optional[Any]         # maps from current version.content_json
    metadata_json: Optional[Any]    # maps from current version.metadata_json
    current_version_id: Optional[UUID]
    version_number: Optional[str]   # from current version
    status: Optional[str]           # maps from current version.external_status
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Older alias kept for any internal usage (not used in new routes)
class VersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: str
    doc_json: Any
    change_summary: Optional[str] = None
    status: str
    metadata_json: Optional[Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DOMAIN MODELS — NATIVE SCHEMA FIELD NAMES
# content_json, external_status, sop_id etc.
# ==========================================

class SOPVersionResponse(BaseModel):
    id: UUID
    sop_id: UUID
    external_version_id: Optional[str] = None
    version_number: str
    external_status: Optional[str] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    content_json: Optional[Any] = None
    metadata_json: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SOPResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    external_id: Optional[str] = None
    sop_number: str
    title: str
    department: Optional[str] = None
    source_system: Optional[str] = None
    is_active: bool
    current_version_id: Optional[UUID] = None
    # Embedded current version for GET /api/sops/{id}
    current_version: Optional[SOPVersionResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviationCreateUpdate(BaseModel):
    title: str
    deviation_number: str
    category: Optional[str] = None
    site: Optional[str] = None
    product_line: Optional[str] = None
    external_status: Optional[str] = None
    description_text: Optional[str] = None
    root_cause_text: Optional[str] = None
    impact_level: Optional[str] = None
    source_system: Optional[str] = None
    event_date: Optional[datetime] = None

class CapaCreateUpdate(BaseModel):
    title: str
    capa_number: str
    external_status: Optional[str] = None
    action_type: Optional[str] = None
    action_text: Optional[str] = None
    effectiveness_text: Optional[str] = None
    owner_name: Optional[str] = None
    due_date: Optional[datetime] = None
    effectiveness_status: Optional[str] = None
    source_system: Optional[str] = None

class AuditFindingCreateUpdate(BaseModel):
    audit_number: Optional[str] = None
    finding_number: Optional[str] = None
    authority: Optional[str] = None
    site: Optional[str] = None
    audit_date: Optional[datetime] = None
    question_text: Optional[str] = None
    finding_text: Optional[str] = None
    response_text: Optional[str] = None
    acceptance_status: Optional[str] = None
    source_system: Optional[str] = None

class DecisionCreateUpdate(BaseModel):
    title: str
    decision_number: Optional[str] = None
    decision_type: Optional[str] = None
    decision_statement: str
    rationale_text: Optional[str] = None
    risk_assessment_text: Optional[str] = None
    alternatives_text: Optional[str] = None
    final_conclusion: Optional[str] = None
    decision_date: Optional[datetime] = None
    decided_by_role: Optional[str] = None
    source_system: Optional[str] = None

class DatasetImportRequest(BaseModel):
    entities: List[dict] # Generic list of entities to import


class DeviationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    external_id: Optional[str] = None
    deviation_number: str
    title: str
    category: Optional[str] = None
    site: Optional[str] = None
    product_line: Optional[str] = None
    external_status: Optional[str] = None
    description_text: Optional[str] = None
    root_cause_text: Optional[str] = None
    impact_level: Optional[str] = None
    source_system: Optional[str] = None
    event_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CapaResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    external_id: Optional[str] = None
    capa_number: str
    title: str
    external_status: Optional[str] = None
    action_type: Optional[str] = None
    action_text: Optional[str] = None
    effectiveness_text: Optional[str] = None
    owner_name: Optional[str] = None
    due_date: Optional[datetime] = None
    effectiveness_status: Optional[str] = None
    source_system: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditFindingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    external_id: Optional[str] = None
    audit_number: Optional[str] = None
    finding_number: Optional[str] = None
    authority: Optional[str] = None
    site: Optional[str] = None
    audit_date: Optional[datetime] = None
    question_text: Optional[str] = None
    finding_text: Optional[str] = None
    response_text: Optional[str] = None
    acceptance_status: Optional[str] = None
    source_system: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    external_id: Optional[str] = None
    decision_number: Optional[str] = None
    decision_type: Optional[str] = None
    title: str
    decision_statement: str
    rationale_text: Optional[str] = None
    risk_assessment_text: Optional[str] = None
    alternatives_text: Optional[str] = None
    final_conclusion: Optional[str] = None
    decision_date: Optional[datetime] = None
    decided_by_role: Optional[str] = None
    source_system: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CONTEXT / RELATED RESPONSES
# ==========================================

class DeviationContextResponse(BaseModel):
    deviation: DeviationResponse
    related_sops: List[SOPResponse] = []
    related_capas: List[CapaResponse] = []
    related_audits: List[AuditFindingResponse] = []
    related_decisions: List[DecisionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SopRelatedResponse(BaseModel):
    sop: SOPResponse
    related_deviations: List[DeviationResponse] = []
    related_capas: List[CapaResponse] = []
    related_audits: List[AuditFindingResponse] = []
    related_decisions: List[DecisionResponse] = []

    model_config = ConfigDict(from_attributes=True)
