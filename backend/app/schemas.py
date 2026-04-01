from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================
# EDITOR COMPATIBILITY LAYER (WRAPPERS)
# ==========================================
class CreateDocumentRequest(BaseModel):
    title: str
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

class VersionResponse(BaseModel):
    id: UUID
    document_id: UUID  # mapped conceptually from sop_id
    version_number: str
    doc_json: Any
    change_summary: Optional[str] = None
    status: str
    metadata_json: Optional[Any]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# DOMAIN MODELS (READ-ONLY)
# ==========================================

class SOPVersionResponse(BaseModel):
    id: UUID
    sop_id: UUID
    external_version_id: Optional[str] = None
    version_number: str
    external_status: Optional[str] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    content_json: Any
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
    created_at: datetime
    updated_at: datetime
    
    versions: Optional[List[SOPVersionResponse]] = None

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

class AuditFindingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
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

    model_config = ConfigDict(from_attributes=True)


class DecisionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
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

    model_config = ConfigDict(from_attributes=True)


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
    related_decisions: List[DecisionResponse] = []

    model_config = ConfigDict(from_attributes=True)
