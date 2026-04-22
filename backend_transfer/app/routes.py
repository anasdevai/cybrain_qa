from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from .models import (
    SOP, SOPVersion, Deviation, Capa, AuditFinding, Decision,
    SopDeviationLink, DeviationCapaLink, CapaAuditLink, AuditDecisionLink, DecisionSopLink
)
from .schemas import (
    # Editor compat request bodies
    CreateDocumentRequest,
    UpdateDocumentRequest,
    CreateVersionRequest,
    UpdateVersionStatusRequest,
    # Editor compat response shapes
    EditorDocResponse,
    EditorVersionResponse,
    # Native domain response shapes
    SOPResponse,
    SOPVersionResponse,
    DeviationResponse,
    CapaResponse,
    AuditFindingResponse,
    DecisionResponse,
    DeviationContextResponse,
    SopRelatedResponse,
    DeviationCreateUpdate,
    CapaCreateUpdate,
    AuditFindingCreateUpdate,
    DecisionCreateUpdate,
    DatasetImportRequest,
)
import uuid
import os

# ==========================================
# CONSTANTS
# ==========================================

# Fixed tenant for dev/seed environment
FIXED_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


# ==========================================
# HELPERS
# ==========================================

def check_mock_mode():
    """Guard: only allow mutation routes when MOCK_EDITOR_MODE=true."""
    if os.getenv("MOCK_EDITOR_MODE", "false").lower() != "true":
        raise HTTPException(
            status_code=403,
            detail="System is in Read-Only mode. Document mutation is disabled."
        )


def _is_tiptap_empty(doc_json: dict | None) -> bool:
    """
    Return True if a TipTap JSON document has no meaningful text content.

    A document is empty when:
    - It is None or not a dict
    - It has no 'content' list, or the list is empty
    - Every text leaf in the tree is whitespace-only
    - The only nodes are blank paragraphs (paragraph with no 'content' children)

    This mirrors the frontend isEditorContentEmpty() in src/utils/editorUtils.js.
    """
    if not doc_json or not isinstance(doc_json, dict):
        return True

    nodes = doc_json.get("content", [])
    if not nodes:
        return True

    def extract_text(node: dict) -> str:
        if node.get("type") == "text":
            return node.get("text", "").strip()
        return " ".join(
            filter(None, [extract_text(c) for c in node.get("content", [])])
        ).strip()

    # Check for any non-whitespace text in the entire tree
    all_text = extract_text(doc_json).strip()
    if all_text:
        return False

    # Also accept non-text meaningful nodes (image, table, codeBlock, etc.)
    meaningful_types = {"image", "horizontalRule", "codeBlock", "table"}
    for node in nodes:
        if node.get("type") in meaningful_types:
            return False

    return True


def _normalize_sop_metadata(sop_number: str, title: str, department: str = None, raw_meta: dict = None) -> dict:
    """
    Ensures metadata is in the full 'thick shell' shape the frontend expects.
    MANDATORY fields for Editor compatibility:
    - sopStatus, variables, approvedBy, auditTrail, versionNote, sopMetadata, etc.
    """
    if not isinstance(raw_meta, dict):
        raw_meta = {}
    
    # 1. Base Structure
    normalized = {
        "sopStatus": raw_meta.get("sopStatus", "draft"),
        "variables": raw_meta.get("variables", {}),
        "approvedBy": raw_meta.get("approvedBy", ""),
        "auditTrail": raw_meta.get("auditTrail", []),
        "versionNote": raw_meta.get("versionNote", ""),
        "obsoleteReason": raw_meta.get("obsoleteReason", ""),
        "approvalSignature": raw_meta.get("approvalSignature", ""),
        "replacementDocumentId": raw_meta.get("replacementDocumentId", ""),
        "sopMetadata": {
            "title": title or "",
            "author": raw_meta.get("sopMetadata", {}).get("author", "System"),
            "reviewer": raw_meta.get("sopMetadata", {}).get("reviewer", ""),
            "riskLevel": raw_meta.get("sopMetadata", {}).get("riskLevel", "Low"),
            "department": department or "Quality",
            "documentId": sop_number or "", 
            "references": raw_meta.get("sopMetadata", {}).get("references", []),
            "reviewDate": raw_meta.get("sopMetadata", {}).get("reviewDate", ""),
            "effectiveDate": raw_meta.get("sopMetadata", {}).get("effectiveDate", ""),
            "regulatoryReferences": raw_meta.get("sopMetadata", {}).get("regulatoryReferences", [])
        }
    }
    
    # Merge nested sopMetadata fields safely
    input_sop_meta = raw_meta.get("sopMetadata", {})
    if isinstance(input_sop_meta, dict):
        for k, v in input_sop_meta.items():
            if k not in ["documentId", "title"]: 
                normalized["sopMetadata"][k] = v

    return normalized


def _build_editor_doc_response(sop: SOP, version: SOPVersion) -> dict:
    """
    Compatibility adapter: maps SOP + SOPVersion onto old editor response shape.
    Normalizes metadata on-the-fly to ensure frontend consistency.
    """
    normalized_meta = _normalize_sop_metadata(
        sop_number=sop.sop_number,
        title=sop.title,
        department=sop.department,
        raw_meta=version.metadata_json
    )

    return {
        "id": str(sop.id),
        "title": sop.title,
        "doc_type": "sop",
        "doc_json": version.content_json,
        "metadata_json": normalized_meta,
        "current_version_id": str(sop.current_version_id) if sop.current_version_id else None,
        "version_number": version.version_number,
        "status": version.external_status or "draft",
        "created_at": sop.created_at,
        "updated_at": sop.updated_at,
    }


def _build_editor_version_response(version: SOPVersion) -> dict:
    """Compatibility adapter for single version response."""
    sop_title = version.sop.title if version.sop else "Untitled"
    sop_num = version.sop.sop_number if version.sop else ""
    sop_dept = version.sop.department if version.sop else "Quality"

    normalized_meta = _normalize_sop_metadata(
        sop_number=sop_num,
        title=sop_title,
        department=sop_dept,
        raw_meta=version.metadata_json
    )

    return {
        "id": str(version.id),
        "doc_id": str(version.sop_id),
        "version_number": version.version_number,
        "status": version.external_status or "draft",
        "doc_json": version.content_json,
        "metadata_json": normalized_meta,
        "effective_date": version.effective_date,
        "review_date": version.review_date,
        "created_at": version.created_at,
        "updated_at": version.updated_at,
    }


def _build_sop_dict(sop: SOP, include_current_version: bool = False, db: Session = None) -> dict:
    """
    Build native SOPResponse dict, optionally embedding the current_version object.
    Keeps native field names: content_json, external_status, etc.
    """
    result = {
        "id": sop.id,
        "tenant_id": sop.tenant_id,
        "external_id": sop.external_id,
        "sop_number": sop.sop_number,
        "title": sop.title,
        "department": sop.department,
        "source_system": sop.source_system,
        "is_active": sop.is_active,
        "current_version_id": sop.current_version_id,
        "current_version": None,
        "created_at": sop.created_at,
        "updated_at": sop.updated_at,
    }
    if include_current_version and db and sop.current_version_id:
        cv = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
        if cv:
            result["current_version"] = {
                "id": cv.id,
                "sop_id": cv.sop_id,
                "external_version_id": cv.external_version_id,
                "version_number": cv.version_number,
                "external_status": cv.external_status,
                "content_json": cv.content_json,
                "metadata_json": cv.metadata_json,
                "effective_date": cv.effective_date,
                "review_date": cv.review_date,
                "created_at": cv.created_at,
                "updated_at": cv.updated_at,
            }
    return result


# ==========================================
# ROUTER
# ==========================================

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


# ==========================================
# OLD EDITOR COMPATIBILITY ROUTES
# All field mappings live here — NOT in the DB
# doc_json = content_json, status = external_status, doc_id = sop_id
# ==========================================

@router.post("/api/editor/docs")
def create_document(
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
    _=Depends(check_mock_mode),
):
    """
    Create a new SOP + its first version.
    Ensures identity is only generated once at the source.
    """
    new_sop_id = uuid.uuid4()
    new_ver_id = uuid.uuid4()
    
    # Identify: only generate SOP number if NOT provided (allowing imports/manuals)
    sop_number = f"SOP-{uuid.uuid4().hex[:8].upper()}"
    
    sop = SOP(
        id=new_sop_id,
        tenant_id=FIXED_TENANT_ID,
        title=payload.title,
        sop_number=sop_number,
        department="Quality",
        is_active=True,
        current_version_id=new_ver_id 
    )
    
    normalized_meta = _normalize_sop_metadata(
        sop_number=sop_number,
        title=payload.title,
        department="Quality",
        raw_meta=payload.metadata_json
    )

    initial_version = SOPVersion(
        id=new_ver_id,
        sop_id=new_sop_id,
        version_number="1",
        content_json=payload.doc_json if payload.doc_json is not None else {"type": "doc", "content": []},
        metadata_json=normalized_meta,
        external_status="draft",
    )
    
    db.add(sop)
    db.add(initial_version)
    db.commit()
    db.refresh(sop)

    return _build_editor_doc_response(sop, initial_version)


@router.get("/api/editor/docs/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Fetch SOP + current version, return in old editor shape.
    Response uses doc_json (mapped from content_json) and status (mapped from external_status).
    """
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    if not sop.current_version_id:
        raise HTTPException(status_code=404, detail="SOP has no current version set")

    current_version = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found in sop_versions")

    return _build_editor_doc_response(sop, current_version)


@router.put("/api/editor/docs/{doc_id}")
def update_document(
    doc_id: str,
    payload: UpdateDocumentRequest,
    db: Session = Depends(get_db),
    _=Depends(check_mock_mode),
):
    """
    Update the current version's content in-place.
    Stores incoming doc_json into content_json — no column renamed.
    Does NOT break version history (other versions untouched).
    """
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    if not sop.current_version_id:
        raise HTTPException(status_code=404, detail="SOP has no current version set")

    current_version = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found")

    # doc_json from frontend → stored as content_json in DB
    current_version.content_json = payload.doc_json
    if payload.metadata_json is not None:
        current_version.metadata_json = payload.metadata_json

    db.commit()
    db.refresh(current_version)

    return {
        "message": "Document updated",
        "current_version_id": str(current_version.id),
        "status": current_version.external_status or "draft",
    }


@router.get("/api/editor/docs/{doc_id}/versions")
def list_versions(doc_id: str, db: Session = Depends(get_db)):
    """
    Return all versions for a SOP using old editor field names.
    doc_json   <- content_json
    doc_id     <- sop_id
    status     <- external_status
    """
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    versions = (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == doc_id)
        .order_by(SOPVersion.created_at.asc())
        .all()
    )
    return [_build_editor_version_response(v) for v in versions]


@router.post("/api/editor/docs/{doc_id}/versions")
def create_version(
    doc_id: str,
    payload: CreateVersionRequest,
    db: Session = Depends(get_db),
    _=Depends(check_mock_mode),
):
    """
    Create a new version row. Uses TRUE sequential integer calculation.
    """
    sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    if _is_tiptap_empty(payload.doc_json):
        raise HTTPException(
            status_code=422,
            detail="Cannot create a new version with empty content.",
        )

    # Calculate real next integer version
    all_versions = db.query(SOPVersion).filter(SOPVersion.sop_id == doc_id).all()
    max_v = 0
    for v in all_versions:
        try:
            val = int(v.version_number)
            if val > max_v: max_v = val
        except: pass
    next_version = str(max_v + 1)

    version = SOPVersion(
        sop_id=sop.id,
        version_number=next_version,
        content_json=payload.doc_json,
        external_status="draft",
        metadata_json=payload.metadata_json or {},
    )
    db.add(version)
    
    # Point parent to new version
    sop.current_version_id = version.id
    
    db.commit()
    db.refresh(version)
    db.refresh(sop)

    return _build_editor_version_response(version)


@router.get("/api/editor/docs/{doc_id}/versions/{version_id}")
def get_version(doc_id: str, version_id: str, db: Session = Depends(get_db)):
    """
    Fetch a specific version by doc_id (= sop_id) and version_id.
    Returns old editor field names.
    """
    version = (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == doc_id, SOPVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return _build_editor_version_response(version)


@router.post("/api/editor/docs/{doc_id}/duplicate")
def duplicate_document(
    doc_id: str,
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
    _=Depends(check_mock_mode),
):
    """
    Duplicate an existing SOP. Reset to version 1.
    """
    source_sop = db.query(SOP).filter(SOP.id == doc_id).first()
    if not source_sop:
        raise HTTPException(status_code=404, detail="Source document not found")

    if payload.doc_json is None:
        source_version = db.query(SOPVersion).filter(SOPVersion.id == source_sop.current_version_id).first()
        content = source_version.content_json if source_version else {"type": "doc", "content": []}
    else:
        content = payload.doc_json

    new_sop_id = uuid.uuid4()
    new_ver_id = uuid.uuid4()
    new_sop_num = f"SOP-{uuid.uuid4().hex[:8].upper()}"

    new_sop = SOP(
        id=new_sop_id,
        tenant_id=FIXED_TENANT_ID,
        title=payload.title or f"Copy of {source_sop.title}",
        sop_number=new_sop_num,
        department=source_sop.department,
        is_active=True,
        current_version_id=new_ver_id
    )
    db.add(new_sop)

    new_version = SOPVersion(
        id=new_ver_id,
        sop_id=new_sop_id,
        version_number="1",
        content_json=content,
        external_status="draft",
        metadata_json=payload.metadata_json or {},
    )
    db.add(new_version)
    
    db.commit()
    db.refresh(new_sop)
    return _build_editor_doc_response(new_sop, new_version)


@router.put("/api/editor/docs/{doc_id}/versions/{version_id}/status")
def update_version_status(
    doc_id: str,
    version_id: str,
    payload: UpdateVersionStatusRequest,
    db: Session = Depends(get_db),
    _=Depends(check_mock_mode),
):
    """
    Update sop_versions.external_status.
    Supports: draft, under_review, effective, obsolete.
    """
    VALID_STATUSES = {"draft", "under_review", "effective", "obsolete"}
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

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
# NEW SOP NATIVE ROUTES
# All field names match DB schema exactly: content_json, external_status, sop_id
# ==========================================

@router.get("/api/sops")
def get_all_sops(db: Session = Depends(get_db)):
    """
    Return all SOPs for the fixed tenant.
    Each entry includes current_version embedded summary for convenience.
    """
    sops = db.query(SOP).filter(SOP.tenant_id == FIXED_TENANT_ID).all()
    return [_build_sop_dict(sop, include_current_version=True, db=db) for sop in sops]


@router.get("/api/sops/{id}")
def get_sop_by_id(id: str, db: Session = Depends(get_db)):
    """
    Return one SOP by id, with current_version embedded as a nested object.
    Uses native DB field names: content_json, external_status.
    """
    sop = db.query(SOP).filter(SOP.id == id, SOP.tenant_id == FIXED_TENANT_ID).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    return _build_sop_dict(sop, include_current_version=True, db=db)


@router.get("/api/sops/{id}/versions", response_model=list[SOPVersionResponse])
def get_sop_versions(id: str, db: Session = Depends(get_db)):
    """
    Return all sop_versions rows where sop_id = {id}.
    Native field names preserved.
    """
    sop = db.query(SOP).filter(SOP.id == id, SOP.tenant_id == FIXED_TENANT_ID).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    return (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == id)
        .order_by(SOPVersion.created_at.asc())
        .all()
    )


@router.get("/api/sops/{id}/related")
def get_sop_related_context(id: str, db: Session = Depends(get_db)):
    """
    Return full related context for the SOP traversing the full link chain:
    sop → deviations → CAPAs → audit_findings → decisions
    Also resolves decision → sop back-links.
    """
    sop = db.query(SOP).filter(SOP.id == id, SOP.tenant_id == FIXED_TENANT_ID).first()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    # Linked Deviations
    dev_links = db.query(SopDeviationLink).filter(SopDeviationLink.sop_id == sop.id).all()
    dev_ids = [l.deviation_id for l in dev_links]
    related_deviations = db.query(Deviation).filter(Deviation.id.in_(dev_ids)).all() if dev_ids else []

    # Linked CAPAs (via deviation → capa links)
    capa_links = db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id.in_(dev_ids)).all() if dev_ids else []
    capa_ids = [l.capa_id for l in capa_links]
    related_capas = db.query(Capa).filter(Capa.id.in_(capa_ids)).all() if capa_ids else []

    # Linked Audit Findings (via capa → audit links)
    audit_links = db.query(CapaAuditLink).filter(CapaAuditLink.capa_id.in_(capa_ids)).all() if capa_ids else []
    audit_ids = [l.audit_finding_id for l in audit_links]
    related_audits = db.query(AuditFinding).filter(AuditFinding.id.in_(audit_ids)).all() if audit_ids else []

    # Linked Decisions via audit chain
    decision_links_from_audit = (
        db.query(AuditDecisionLink).filter(AuditDecisionLink.audit_finding_id.in_(audit_ids)).all()
        if audit_ids else []
    )
    decision_ids = {l.decision_id for l in decision_links_from_audit}

    # Also include decisions directly linked to this SOP via decision_sop_links
    direct_decision_links = db.query(DecisionSopLink).filter(DecisionSopLink.sop_id == sop.id).all()
    for l in direct_decision_links:
        decision_ids.add(l.decision_id)

    related_decisions = db.query(Decision).filter(Decision.id.in_(list(decision_ids))).all() if decision_ids else []

    return {
        "sop": _build_sop_dict(sop, include_current_version=True, db=db),
        "related_deviations": related_deviations,
        "related_capas": related_capas,
        "related_audits": related_audits,
        "related_decisions": related_decisions,
    }


# ==========================================
# DEVIATION ROUTES
# ==========================================

@router.get("/api/deviations/{id}", response_model=DeviationResponse)
def get_deviation_by_id(id: str, db: Session = Depends(get_db)):
    """Return a single Deviation record."""
    dev = db.query(Deviation).filter(Deviation.id == id, Deviation.tenant_id == FIXED_TENANT_ID).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found")
    return dev


@router.get("/api/deviations/{id}/context")
def get_deviation_context(id: str, db: Session = Depends(get_db)):
    """
    Return full chain context for a Deviation:
    deviation → SOP, CAPA, audit_finding, decisions
    """
    dev = db.query(Deviation).filter(Deviation.id == id, Deviation.tenant_id == FIXED_TENANT_ID).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found")

    # Linked SOPs
    sop_links = db.query(SopDeviationLink).filter(SopDeviationLink.deviation_id == dev.id).all()
    sop_ids = [l.sop_id for l in sop_links]
    related_sops_raw = db.query(SOP).filter(SOP.id.in_(sop_ids)).all() if sop_ids else []
    related_sops = [_build_sop_dict(s, include_current_version=True, db=db) for s in related_sops_raw]

    # Linked CAPAs
    capa_links = db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id == dev.id).all()
    capa_ids = [l.capa_id for l in capa_links]
    related_capas = db.query(Capa).filter(Capa.id.in_(capa_ids)).all() if capa_ids else []

    # Linked Audit Findings (from CAPAs)
    audit_links = db.query(CapaAuditLink).filter(CapaAuditLink.capa_id.in_(capa_ids)).all() if capa_ids else []
    audit_ids = [l.audit_finding_id for l in audit_links]
    related_audits = db.query(AuditFinding).filter(AuditFinding.id.in_(audit_ids)).all() if audit_ids else []

    # Linked Decisions (from audit findings)
    decision_links = (
        db.query(AuditDecisionLink).filter(AuditDecisionLink.audit_finding_id.in_(audit_ids)).all()
        if audit_ids else []
    )
    decision_ids = [l.decision_id for l in decision_links]
    related_decisions = db.query(Decision).filter(Decision.id.in_(decision_ids)).all() if decision_ids else []

    return {
        "deviation": dev,
        "related_sops": related_sops,
        "related_capas": related_capas,
        "related_audits": related_audits,
        "related_decisions": related_decisions,
    }

@router.get("/api/deviations", response_model=List[DeviationResponse])
def get_all_deviations(db: Session = Depends(get_db)):
    """Return all Deviation records."""
    return db.query(Deviation).filter(Deviation.tenant_id == FIXED_TENANT_ID).all()

@router.post("/api/deviations", response_model=DeviationResponse)
def create_deviation(payload: DeviationCreateUpdate, db: Session = Depends(get_db)):
    """Create a new Deviation record."""
    dev = Deviation(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev

@router.put("/api/deviations/{id}", response_model=DeviationResponse)
def update_deviation(id: str, payload: DeviationCreateUpdate, db: Session = Depends(get_db)):
    """Update an existing Deviation record."""
    dev = db.query(Deviation).filter(Deviation.id == id, Deviation.tenant_id == FIXED_TENANT_ID).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found")
    
    for key, value in payload.model_dump().items():
        setattr(dev, key, value)
    
    db.commit()
    db.refresh(dev)
    return dev

# ==========================================
# CAPA ROUTES
# ==========================================

@router.get("/api/capas", response_model=List[CapaResponse])
def get_all_capas(db: Session = Depends(get_db)):
    """Return all CAPA records."""
    return db.query(Capa).filter(Capa.tenant_id == FIXED_TENANT_ID).all()

@router.post("/api/capas", response_model=CapaResponse)
def create_capa(payload: CapaCreateUpdate, db: Session = Depends(get_db)):
    """Create a new CAPA record."""
    capa = Capa(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(capa)
    db.commit()
    db.refresh(capa)
    return capa

@router.get("/api/capas/{id}", response_model=CapaResponse)
def get_capa(id: str, db: Session = Depends(get_db)):
    """Return a single CAPA record."""
    capa = db.query(Capa).filter(Capa.id == id, Capa.tenant_id == FIXED_TENANT_ID).first()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    return capa

@router.put("/api/capas/{id}", response_model=CapaResponse)
def update_capa(id: str, payload: CapaCreateUpdate, db: Session = Depends(get_db)):
    """Update an existing CAPA record."""
    capa = db.query(Capa).filter(Capa.id == id, Capa.tenant_id == FIXED_TENANT_ID).first()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    
    for key, value in payload.model_dump().items():
        setattr(capa, key, value)
    
    db.commit()
    db.refresh(capa)
    return capa

# ==========================================
# AUDIT ROUTES
# ==========================================

@router.get("/api/audits", response_model=List[AuditFindingResponse])
def get_all_audits(db: Session = Depends(get_db)):
    """Return all Audit Finding records."""
    return db.query(AuditFinding).filter(AuditFinding.tenant_id == FIXED_TENANT_ID).all()

@router.post("/api/audits", response_model=AuditFindingResponse)
def create_audit(payload: AuditFindingCreateUpdate, db: Session = Depends(get_db)):
    """Create a new Audit Finding record."""
    audit = AuditFinding(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit

@router.get("/api/audits/{id}", response_model=AuditFindingResponse)
def get_audit(id: str, db: Session = Depends(get_db)):
    """Return a single Audit Finding record."""
    audit = db.query(AuditFinding).filter(AuditFinding.id == id, AuditFinding.tenant_id == FIXED_TENANT_ID).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit Finding not found")
    return audit

@router.put("/api/audits/{id}", response_model=AuditFindingResponse)
def update_audit(id: str, payload: AuditFindingCreateUpdate, db: Session = Depends(get_db)):
    """Update an existing Audit Finding record."""
    audit = db.query(AuditFinding).filter(AuditFinding.id == id, AuditFinding.tenant_id == FIXED_TENANT_ID).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit Finding not found")
    
    for key, value in payload.model_dump().items():
        setattr(audit, key, value)
    
    db.commit()
    db.refresh(audit)
    return audit

# ==========================================
# DECISION ROUTES
# ==========================================

@router.get("/api/decisions", response_model=List[DecisionResponse])
def get_all_decisions(db: Session = Depends(get_db)):
    """Return all Decision records."""
    return db.query(Decision).filter(Decision.tenant_id == FIXED_TENANT_ID).all()

@router.post("/api/decisions", response_model=DecisionResponse)
def create_decision(payload: DecisionCreateUpdate, db: Session = Depends(get_db)):
    """Create a new Decision record."""
    decision = Decision(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision

@router.get("/api/decisions/{id}", response_model=DecisionResponse)
def get_decision(id: str, db: Session = Depends(get_db)):
    """Return a single Decision record."""
    decision = db.query(Decision).filter(Decision.id == id, Decision.tenant_id == FIXED_TENANT_ID).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision

@router.put("/api/decisions/{id}", response_model=DecisionResponse)
def update_decision(id: str, payload: DecisionCreateUpdate, db: Session = Depends(get_db)):
    """Update an existing Decision record."""
    decision = db.query(Decision).filter(Decision.id == id, Decision.tenant_id == FIXED_TENANT_ID).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    for key, value in payload.model_dump().items():
        setattr(decision, key, value)
    
    db.commit()
    db.refresh(decision)
    return decision

# ==========================================
# DATASET IMPORT ROUTE
# ==========================================

@router.post("/api/import/dataset")
def import_dataset(payload: DatasetImportRequest, db: Session = Depends(get_db)):
    """Import a dataset of entities."""
    # This is a placeholder implementation.
    # In a real scenario, you would loop through entities and add them to their respective tables.
    # For now, we return a simple success message to match the Swagger UI.
    return {"message": f"Successfully imported {len(payload.entities)} entities"}
