from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from .models import (
    SOP, SOPVersion, Deviation, Capa, AuditFinding, Decision,
    SopDeviationLink, DeviationCapaLink, CapaAuditLink, AuditDecisionLink, DecisionSopLink
)
from .schemas import (
    CreateDocumentRequest,
    UpdateDocumentRequest,
    CreateVersionRequest,
    UpdateVersionStatusRequest,
    VersionResponse,
    SOPResponse,
    DeviationResponse,
    DeviationContextResponse,
    SOPVersionResponse,
    SopRelatedResponse
)
import uuid
import os

def check_mock_mode():
    if os.getenv("MOCK_EDITOR_MODE", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="System is in Read-Only mode. Document mutation is disabled.")

# Fixed Tenant for Dev
FIXED_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

# ==========================================
# EDITOR COMPATIBILITY LAYER
# ==========================================
@router.post("/api/editor/docs")
def create_document(payload: CreateDocumentRequest, db: Session = Depends(get_db), _ = Depends(check_mock_mode)):
    sop = SOP(
        tenant_id=FIXED_TENANT_ID,
        title=payload.title,
        sop_number=f"SOP-NEW-{uuid.uuid4().hex[:6].upper()}",
        department="Quality", # Defaulting for UI compat
        is_active=True
    )
    db.add(sop)
    db.commit()
    db.refresh(sop)

    initial_version = SOPVersion(
        sop_id=sop.id,
        version_number="1",
        content_json=payload.doc_json if payload.doc_json is not None else {"type": "doc", "content": []}, # UI doc_json equivalent
        metadata_json=payload.metadata_json if payload.metadata_json is not None else {},
        external_status="draft" # UI fallback for draft
    )
    db.add(initial_version)
    db.commit()
    db.refresh(initial_version)

    sop.current_version_id = initial_version.id
    db.commit()
    db.refresh(sop)

    return {
        "id": str(sop.id),
        "title": sop.title,
        "profile": "sop", # generic UI compat
        "current_version_id": str(sop.current_version_id),
    }

@router.get("/api/editor/docs/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
    if not current_version:
        # Fallback if no version is found somehow
        raise HTTPException(status_code=404, detail="Current version not found")

    return {
        "id": str(sop.id),
        "title": sop.title,
        "profile": "sop",
        "current_version_id": str(sop.current_version_id),
        "current_version": {
            "id": str(current_version.id),
            "document_id": str(current_version.sop_id), # mapped
            "version_number": current_version.version_number,
            "doc_json": current_version.content_json, # mapped
            "change_summary": None,
            "status": current_version.external_status or "draft",
            "metadata_json": current_version.metadata_json,
            "created_at": current_version.created_at,
        }
    }

@router.put("/api/editor/docs/{doc_id}")
def update_document(doc_id: str, payload: UpdateDocumentRequest, db: Session = Depends(get_db), _ = Depends(check_mock_mode)):
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found")

    current_version.content_json = payload.doc_json
    if payload.metadata_json is not None:
        current_version.metadata_json = payload.metadata_json

    db.commit()
    db.refresh(current_version)

    return {"message": "Document updated", "current_version_id": str(current_version.id)}


@router.get("/api/editor/docs/{doc_id}/versions")
def list_versions(doc_id: str, db: Session = Depends(get_db)):
    versions = (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == doc_id)
        .order_by(SOPVersion.created_at.asc())
        .all()
    )

    return [
        {
            "id": str(v.id),
            "document_id": str(v.sop_id),
            "version_number": v.version_number, # now a string
            "doc_json": v.content_json,
            "status": v.external_status or "draft",
            "change_summary": None,
            "metadata_json": v.metadata_json,
            "created_at": v.created_at,
        }
        for v in versions
    ]

@router.post("/api/editor/docs/{doc_id}/versions")
def create_version(doc_id: str, payload: CreateVersionRequest, db: Session = Depends(get_db), _ = Depends(check_mock_mode)):
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    # Simple version calculation for compat
    versions_count = db.query(func.count(SOPVersion.id)).filter(SOPVersion.sop_id == doc_id).scalar()
    next_version = str(versions_count + 1)

    version = SOPVersion(
        sop_id=sop.id,
        version_number=next_version,
        content_json=payload.doc_json,
        external_status="draft",
        metadata_json=payload.metadata_json or {},
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    sop.current_version_id = version.id
    db.commit()

    return {
        "id": str(version.id),
        "document_id": str(version.sop_id),
        "version_number": version.version_number,
        "status": version.external_status,
    }

@router.get("/api/editor/docs/{doc_id}/versions/{version_id}")
def get_version(doc_id: str, version_id: str, db: Session = Depends(get_db)):
    version = (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == doc_id, SOPVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return {
        "id": str(version.id),
        "document_id": str(version.sop_id),
        "version_number": version.version_number,
        "doc_json": version.content_json,
        "change_summary": None,
        "status": version.external_status or "draft",
        "metadata_json": version.metadata_json,
        "created_at": version.created_at,
    }

@router.put("/api/editor/docs/{doc_id}/versions/{version_id}/status")
def update_version_status(doc_id: str, version_id: str, payload: UpdateVersionStatusRequest, db: Session = Depends(get_db), _ = Depends(check_mock_mode)):
    version = (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == doc_id, SOPVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    version.external_status = payload.status
    if payload.metadata_json is not None:
        version.metadata_json = payload.metadata_json

    db.commit()
    db.refresh(version)

    return {
        "message": "Version status updated",
        "id": str(version.id),
        "status": version.external_status,
    }

# ==========================================
# DOMAIN MODELS (READ-ONLY)
# ==========================================

@router.get("/api/sops", response_model=list[SOPResponse])
def get_all_sops(db: Session = Depends(get_db)):
    return db.query(SOP).filter(SOP.tenant_id == FIXED_TENANT_ID).all()

@router.get("/api/sops/{id}", response_model=SOPResponse)
def get_sop_by_id(id: str, db: Session = Depends(get_db)):
    sop = db.query(SOP).filter(SOP.id == id, SOP.tenant_id == FIXED_TENANT_ID).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    return sop

@router.get("/api/sops/{id}/versions", response_model=list[SOPVersionResponse])
def get_sop_versions(id: str, db: Session = Depends(get_db)):
    return db.query(SOPVersion).filter(SOPVersion.sop_id == id).all()

@router.get("/api/deviations/{id}", response_model=DeviationResponse)
def get_deviation_by_id(id: str, db: Session = Depends(get_db)):
    dev = db.query(Deviation).filter(Deviation.id == id, Deviation.tenant_id == FIXED_TENANT_ID).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found")
    return dev

@router.get("/api/deviations/{id}/context", response_model=DeviationContextResponse)
def get_deviation_context(id: str, db: Session = Depends(get_db)):
    dev = db.query(Deviation).filter(Deviation.id == id, Deviation.tenant_id == FIXED_TENANT_ID).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found")

    # Linked SOPs
    sop_links = db.query(SopDeviationLink).filter(SopDeviationLink.deviation_id == dev.id).all()
    related_sops = db.query(SOP).filter(SOP.id.in_([l.sop_id for l in sop_links])).all() if sop_links else []

    # Linked CAPAs
    capa_links = db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id == dev.id).all()
    related_capas = db.query(Capa).filter(Capa.id.in_([l.capa_id for l in capa_links])).all() if capa_links else []

    # Find Audits from those Capas
    capa_ids = [c.id for c in related_capas]
    audit_links = db.query(CapaAuditLink).filter(CapaAuditLink.capa_id.in_(capa_ids)).all() if capa_ids else []
    related_audits = db.query(AuditFinding).filter(AuditFinding.id.in_([l.audit_finding_id for l in audit_links])).all() if audit_links else []

    # Find Decisions from Audits
    audit_ids = [a.id for a in related_audits]
    decision_links = db.query(AuditDecisionLink).filter(AuditDecisionLink.audit_finding_id.in_(audit_ids)).all() if audit_ids else []
    related_decisions = db.query(Decision).filter(Decision.id.in_([l.decision_id for l in decision_links])).all() if decision_links else []

    return {
        "deviation": dev,
        "related_sops": related_sops,
        "related_capas": related_capas,
        "related_audits": related_audits,
        "related_decisions": related_decisions
    }

@router.get("/api/sops/{id}/related", response_model=SopRelatedResponse)
def get_sop_related_context(id: str, db: Session = Depends(get_db)):
    sop = db.query(SOP).filter(SOP.id == id, SOP.tenant_id == FIXED_TENANT_ID).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    dev_links = db.query(SopDeviationLink).filter(SopDeviationLink.sop_id == sop.id).all()
    related_deviations = db.query(Deviation).filter(Deviation.id.in_([l.deviation_id for l in dev_links])).all() if dev_links else []

    decision_links = db.query(DecisionSopLink).filter(DecisionSopLink.sop_id == sop.id).all()
    related_decisions = db.query(Decision).filter(Decision.id.in_([l.decision_id for l in decision_links])).all() if decision_links else []

    return {
        "sop": sop,
        "related_deviations": related_deviations,
        "related_decisions": related_decisions
    }
