from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, ForeignKey, func, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import Base
from sqlalchemy.orm import relationship
import uuid

# Re-use existing tables logic but completely swap out the models

class SOP(Base):
    __tablename__ = "sops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255), nullable=True)
    sop_number = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    source_system = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # We add this purely for UI Editor compatibility mapping. The domain schema doesn't strictly need it to find versions, but it helps the editor mock workflow.
    current_version_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    versions = relationship("SOPVersion", back_populates="sop", cascade="all, delete-orphan")


class SOPVersion(Base):
    __tablename__ = "sop_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sop_id = Column(UUID(as_uuid=True), ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    external_version_id = Column(String(100), nullable=True)
    version_number = Column(String(50), nullable=False)
    external_status = Column(String(50), nullable=True)
    effective_date = Column(TIMESTAMP, nullable=True)
    review_date = Column(TIMESTAMP, nullable=True)
    content_json = Column(JSONB, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    superseded_by_version_id = Column(UUID(as_uuid=True), ForeignKey("sop_versions.id"), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    sop = relationship("SOP", back_populates="versions")

class Deviation(Base):
    __tablename__ = "deviations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255), nullable=True)
    deviation_number = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    site = Column(String(100), nullable=True)
    product_line = Column(String(100), nullable=True)
    external_status = Column(String(50), nullable=True)
    description_text = Column(Text, nullable=True)
    root_cause_text = Column(Text, nullable=True)
    impact_level = Column(String(50), nullable=True)
    source_system = Column(String(100), nullable=True)
    event_date = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

class Capa(Base):
    __tablename__ = "capas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255), nullable=True)
    capa_number = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    external_status = Column(String(50), nullable=True)
    action_type = Column(String(50), nullable=True)
    action_text = Column(Text, nullable=True)
    effectiveness_text = Column(Text, nullable=True)
    owner_name = Column(String(255), nullable=True)
    due_date = Column(TIMESTAMP, nullable=True)
    effectiveness_status = Column(String(50), nullable=True)
    source_system = Column(String(100), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255), nullable=True)
    audit_number = Column(String(100), nullable=True)
    finding_number = Column(String(100), nullable=True)
    authority = Column(String(100), nullable=True)
    site = Column(String(100), nullable=True)
    audit_date = Column(TIMESTAMP, nullable=True)
    question_text = Column(Text, nullable=True)
    finding_text = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)
    acceptance_status = Column(String(50), nullable=True)
    source_system = Column(String(100), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255), nullable=True)
    decision_number = Column(String(100), nullable=True)
    decision_type = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    decision_statement = Column(Text, nullable=False)
    rationale_text = Column(Text, nullable=True)
    risk_assessment_text = Column(Text, nullable=True)
    alternatives_text = Column(Text, nullable=True)
    final_conclusion = Column(Text, nullable=True)
    decision_date = Column(TIMESTAMP, nullable=True)
    decided_by_role = Column(String(100), nullable=True)
    source_system = Column(String(100), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

# Link Tables
class SopDeviationLink(Base):
    __tablename__ = "sop_deviation_links"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    sop_id = Column(UUID(as_uuid=True), ForeignKey("sops.id"), nullable=False)
    deviation_id = Column(UUID(as_uuid=True), ForeignKey("deviations.id"), nullable=False)
    link_reason = Column(String(100), nullable=True)
    rationale_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class DeviationCapaLink(Base):
    __tablename__ = "deviation_capa_links"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    deviation_id = Column(UUID(as_uuid=True), ForeignKey("deviations.id"), nullable=False)
    capa_id = Column(UUID(as_uuid=True), ForeignKey("capas.id"), nullable=False)
    link_reason = Column(String(100), nullable=True)
    rationale_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class CapaAuditLink(Base):
    __tablename__ = "capa_audit_links"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    capa_id = Column(UUID(as_uuid=True), ForeignKey("capas.id"), nullable=False)
    audit_finding_id = Column(UUID(as_uuid=True), ForeignKey("audit_findings.id"), nullable=False)
    link_reason = Column(String(100), nullable=True)
    rationale_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class AuditDecisionLink(Base):
    __tablename__ = "audit_decision_links"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    audit_finding_id = Column(UUID(as_uuid=True), ForeignKey("audit_findings.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=False)
    link_reason = Column(String(100), nullable=True)
    rationale_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class DecisionSopLink(Base):
    __tablename__ = "decision_sop_links"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=False)
    sop_id = Column(UUID(as_uuid=True), ForeignKey("sops.id"), nullable=False)
    sop_version_id = Column(UUID(as_uuid=True), ForeignKey("sop_versions.id"), nullable=True)
    link_reason = Column(String(100), nullable=True)
    rationale_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

# Supporting Tables
class SourceReference(Base):
    __tablename__ = "source_references"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    reference_type = Column(String(50), nullable=False)
    reference_label = Column(String(255), nullable=True)
    reference_value = Column(String(255), nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_version_id = Column(UUID(as_uuid=True), nullable=True)
    chunk_type = Column(String(50), nullable=True)
    block_id = Column(String(100), nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class LifecycleConfig(Base):
    __tablename__ = "lifecycle_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False) # e.g., 'sop', 'deviation'
    config_json = Column(JSONB, nullable=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
