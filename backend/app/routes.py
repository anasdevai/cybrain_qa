from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from .database import get_db
from .models import (
    SOP, SOPVersion, Deviation, Capa, AuditFinding, Decision,
    SopDeviationLink, DeviationCapaLink, CapaAuditLink, AuditDecisionLink, DecisionSopLink,
    AILinkSuggestion
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
    LinkRequest,
    SemanticReindexRequest,
    LinkSuggestionResponse,
    SemanticStatusResponse,
)
from .services.semantic_pipeline import SemanticPipelineService, ENTITY_TYPES
from uuid import UUID
import uuid
import os
from datetime import datetime

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
    # Default to enabled in local/dev so editor save/version actions work
    # unless explicitly disabled by environment configuration.
    if os.getenv("MOCK_EDITOR_MODE", "true").lower() != "true":
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


def _tenant_scoped_query(db: Session, model):
    """
    Default to inclusive query in local/dev so records inserted directly
    (with varying tenant_id values) and records imported through dataset flow
    are both visible to frontend APIs.

    Set STRICT_TENANT_SCOPING=true to enforce fixed-tenant-only behavior.
    """
    strict_tenant = os.getenv("STRICT_TENANT_SCOPING", "false").lower() == "true"
    scoped = db.query(model).filter(model.tenant_id == FIXED_TENANT_ID)
    if strict_tenant:
        return scoped
    return db.query(model)


def _resolve_sop_lookup(db: Session, sop_ref: str):
    """
    Resolve SOP by UUID or SOP number while respecting tenant fallback logic.
    """
    base_query = _tenant_scoped_query(db, SOP)
    try:
        id_val = uuid.UUID(sop_ref)
        return base_query.filter(SOP.id == id_val).first()
    except ValueError:
        return base_query.filter(SOP.sop_number == sop_ref).first()


def _resolve_current_version(db: Session, sop: SOP) -> SOPVersion | None:
    """
    Return SOP current version with a safe fallback for imported records
    where current_version_id may be missing but version rows exist.
    """
    if sop.current_version_id:
        current = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first()
        if current:
            return current

    latest = (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == sop.id)
        .order_by(SOPVersion.created_at.desc())
        .first()
    )
    if latest:
        sop.current_version_id = latest.id
        db.commit()
        db.refresh(sop)
        return latest

    # Last-resort bootstrap: create an initial editor-compatible draft version
    # so legacy/imported SOP rows without versions can still be opened/edited.
    initial_version = SOPVersion(
        id=uuid.uuid4(),
        sop_id=sop.id,
        version_number="1",
        content_json={"type": "doc", "content": []},
        metadata_json=_normalize_sop_metadata(
            sop_number=sop.sop_number,
            title=sop.title,
            department=sop.department,
            raw_meta={},
        ),
        external_status="draft",
    )
    db.add(initial_version)
    sop.current_version_id = initial_version.id
    db.commit()
    db.refresh(sop)
    db.refresh(initial_version)
    return initial_version


def _schedule_semantic_job(background_tasks: BackgroundTasks, entity_type: str, entity_id: uuid.UUID, version_id: uuid.UUID | None = None, job_type: str = "entity_reindex"):
    if entity_type not in ENTITY_TYPES:
        return
    SemanticPipelineService.enqueue_reindex(
        entity_type=entity_type,
        entity_id=entity_id,
        version_id=version_id,
        job_type=job_type,
    )


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
        "auditTrail": raw_meta.get("auditTrail") if isinstance(raw_meta.get("auditTrail"), list) else [],
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
    Standardizes metadata to the 'thick shell' format.
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
            normalized_meta = _normalize_sop_metadata(
                sop_number=sop.sop_number,
                title=sop.title,
                department=sop.department,
                raw_meta=cv.metadata_json
            )
            result["current_version"] = {
                "id": cv.id,
                "sop_id": cv.sop_id,
                "external_version_id": cv.external_version_id,
                "version_number": cv.version_number,
                "external_status": cv.external_status,
                "content_json": cv.content_json,
                "metadata_json": normalized_meta,
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


@router.get("/api/health")
def health():
    return {"status": "ok"}


# ==========================================
# OLD EDITOR COMPATIBILITY ROUTES
# All field mappings live here — NOT in the DB
# doc_json = content_json, status = external_status, doc_id = sop_id
# ==========================================

@router.post("/api/editor/docs", response_model=EditorDocResponse)
def create_document(
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _=Depends(check_mock_mode),
):
    """
    Create a new SOP + its first version.
    Ensures identity is only generated once at the source.
    """
    new_sop_id = uuid.uuid4()
    new_ver_id = uuid.uuid4()
    
    # Identify: only generate SOP number if NOT provided 
    sop_number = payload.metadata_json.get("sopMetadata", {}).get("documentId") if payload.metadata_json else None
    if not sop_number:
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

    if background_tasks:
        _schedule_semantic_job(background_tasks, "sop", sop.id, initial_version.id)
    return _build_editor_doc_response(sop, initial_version)


@router.get("/api/editor/docs/{doc_id}", response_model=EditorDocResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Fetch SOP + current version, return in old editor shape.
    Response uses doc_json (mapped from content_json) and status (mapped from external_status).
    """
    # Handle lookup by either UUID (id) or SOP Number
    sop = None
    try:
        id_val = uuid.UUID(doc_id)
        sop = db.query(SOP).filter(SOP.id == id_val).first()
    except ValueError:
        sop = db.query(SOP).filter(SOP.sop_number == doc_id).first()

    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = _resolve_current_version(db, sop)
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found in sop_versions")

    return _build_editor_doc_response(sop, current_version)


@router.put("/api/editor/docs/{doc_id}", response_model=EditorDocResponse)
def update_document(
    doc_id: str,
    payload: UpdateDocumentRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _=Depends(check_mock_mode),
):
    """
    Update the current version's content in-place.
    Stores incoming doc_json into content_json — no column renamed.
    Does NOT break version history (other versions untouched).
    """
    # Handle lookup by either UUID (id) or SOP Number
    sop = None
    try:
        id_val = uuid.UUID(doc_id)
        sop = db.query(SOP).filter(SOP.id == id_val).first()
    except ValueError:
        sop = db.query(SOP).filter(SOP.sop_number == doc_id).first()

    if not sop:
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = _resolve_current_version(db, sop)
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found")

    # doc_json from frontend → stored as content_json in DB
    current_version.content_json = payload.doc_json
    if payload.metadata_json is not None:
        current_version.metadata_json = payload.metadata_json

    db.commit()
    db.refresh(current_version)

    if background_tasks:
        _schedule_semantic_job(background_tasks, "sop", sop.id, current_version.id)
    return _build_editor_doc_response(sop, current_version)


@router.get("/api/editor/docs/{doc_id}/versions", response_model=List[EditorVersionResponse])
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


@router.post("/api/editor/docs/{doc_id}/versions", response_model=EditorVersionResponse)
def create_version(
    doc_id: str,
    payload: CreateVersionRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
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
    
    # Store justification in metadata if provided
    if payload.change_justification:
        meta_dict = dict(version.metadata_json) if version.metadata_json else {}
        audit_trail = meta_dict.get("auditTrail", [])
        if not isinstance(audit_trail, list):
            audit_trail = []
        audit_trail.append({
            "action": "created_new_revision",
            "note": payload.change_justification,
            "version": next_version,
            "createdAt": datetime.utcnow().isoformat(),
            "actor": "System"
        })
        meta_dict["auditTrail"] = audit_trail
        meta_dict["change_justification"] = payload.change_justification
        version.metadata_json = meta_dict

    db.commit()
    db.refresh(version)
    db.refresh(sop)

    if background_tasks:
        _schedule_semantic_job(background_tasks, "sop", sop.id, version.id)
    return _build_editor_version_response(version)


@router.get("/api/editor/docs/{doc_id}/versions/{version_id}", response_model=EditorVersionResponse)
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


@router.post("/api/editor/docs/{doc_id}/duplicate", response_model=EditorDocResponse)
def duplicate_document(
    doc_id: str,
    payload: CreateDocumentRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
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
    
    # CRITICAL: Link parent SOP's current_version_id back to this new version
    new_sop.current_version_id = new_ver_id
    
    db.commit()
    db.refresh(new_sop)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "sop", new_sop.id, new_version.id)
    return _build_editor_doc_response(new_sop, new_version)


@router.put("/api/editor/docs/{doc_id}/versions/{version_id}/status", response_model=EditorVersionResponse)
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

    return _build_editor_version_response(version)


# ==========================================
# NEW SOP NATIVE ROUTES
# All field names match DB schema exactly: content_json, external_status, sop_id
# ==========================================

@router.get("/api/sops", response_model=List[SOPResponse])
def get_all_sops(db: Session = Depends(get_db)):
    """
    Return all SOPs for the fixed tenant.
    Each entry includes current_version embedded summary for convenience.
    """
    sops = _tenant_scoped_query(db, SOP).all()
    return [_build_sop_dict(sop, include_current_version=True, db=db) for sop in sops]


@router.get("/api/sops/{id}", response_model=SOPResponse)
def get_sop_by_id(id: str, db: Session = Depends(get_db)):
    """
    Return one SOP by id, with current_version embedded as a nested object.
    Uses native DB field names: content_json, external_status.
    """
    sop = _resolve_sop_lookup(db, id)

    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    return _build_sop_dict(sop, include_current_version=True, db=db)


@router.get("/api/sops/{id}/versions", response_model=list[SOPVersionResponse])
def get_sop_versions(id: str, db: Session = Depends(get_db)):
    """
    Return all sop_versions rows where sop_id = {id}.
    Native field names preserved.
    """
    sop = _resolve_sop_lookup(db, id)

    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    return (
        db.query(SOPVersion)
        .filter(SOPVersion.sop_id == sop.id)
        .order_by(SOPVersion.created_at.asc())
        .all()
    )


@router.get("/api/sops/{id}/related", response_model=SopRelatedResponse)
def get_sop_related_context(id: str, db: Session = Depends(get_db)):
    """
    Return full related context for the SOP traversing the full link chain:
    sop → deviations → CAPAs → audit_findings → decisions
    Also resolves decision → sop back-links.
    """
    # Handle lookup by either UUID (id) or SOP Number
    sop = _resolve_sop_lookup(db, id)

    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")

    # 1. Deviations linked to SOP
    dev_links = db.query(SopDeviationLink).filter(SopDeviationLink.sop_id == sop.id).all()
    dev_ids = {l.deviation_id for l in dev_links}

    # 2. Decisions directly linked to SOP
    direct_decision_links = db.query(DecisionSopLink).filter(DecisionSopLink.sop_id == sop.id).all()
    decision_ids = {l.decision_id for l in direct_decision_links}

    # 3. Traversal: expand from decisions (Decision → Audit → CAPA → Deviation)
    audit_ids = set()
    if decision_ids:
        audit_links = db.query(AuditDecisionLink).filter(AuditDecisionLink.decision_id.in_(list(decision_ids))).all()
        audit_ids = {l.audit_finding_id for l in audit_links}

    # 4. Traversal: expand from deviations (Deviation → CAPA → Audit → Decision)
    capa_ids = set()
    if dev_ids:
        capa_links = db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id.in_(list(dev_ids))).all()
        capa_ids = {l.capa_id for l in capa_links}

    # 5. Connect CAPAs and Audits (Bidirectional)
    if capa_ids:
        ca_links = db.query(CapaAuditLink).filter(CapaAuditLink.capa_id.in_(list(capa_ids))).all()
        for l in ca_links:
            audit_ids.add(l.audit_finding_id)
            
    if audit_ids:
        ac_links = db.query(CapaAuditLink).filter(CapaAuditLink.audit_finding_id.in_(list(audit_ids))).all()
        for l in ac_links:
            capa_ids.add(l.capa_id)

    # 6. Re-expand from CAPAs to Deviations (Reverse)
    if capa_ids:
        cd_links = db.query(DeviationCapaLink).filter(DeviationCapaLink.capa_id.in_(list(capa_ids))).all()
        for l in cd_links:
            dev_ids.add(l.deviation_id)

    # 7. Final expansion for Decisions from Audits
    if audit_ids:
        ad_links = db.query(AuditDecisionLink).filter(AuditDecisionLink.audit_finding_id.in_(list(audit_ids))).all()
        for l in ad_links:
            decision_ids.add(l.decision_id)

    # 8. SOP-to-SOP chaining via shared decisions:
    # gather all SOPs connected to the expanded decision set
    related_sop_ids = set()
    if decision_ids:
        decision_sop_links = db.query(DecisionSopLink).filter(DecisionSopLink.decision_id.in_(list(decision_ids))).all()
        for link in decision_sop_links:
            if link.sop_id != sop.id:
                related_sop_ids.add(link.sop_id)

    # include incoming reverse links to this SOP as additional chaining evidence
    incoming_links = db.query(DecisionSopLink).filter(DecisionSopLink.sop_id == sop.id).all()
    incoming_decision_ids = {l.decision_id for l in incoming_links}
    if incoming_decision_ids:
        sibling_sop_links = db.query(DecisionSopLink).filter(DecisionSopLink.decision_id.in_(list(incoming_decision_ids))).all()
        for link in sibling_sop_links:
            if link.sop_id != sop.id:
                related_sop_ids.add(link.sop_id)

    related_sops_raw = _tenant_scoped_query(db, SOP).filter(SOP.id.in_(list(related_sop_ids))).all() if related_sop_ids else []
    related_sops = [_build_sop_dict(item, include_current_version=True, db=db) for item in related_sops_raw]

    related_deviations = db.query(Deviation).filter(Deviation.id.in_(list(dev_ids))).all() if dev_ids else []
    related_capas = db.query(Capa).filter(Capa.id.in_(list(capa_ids))).all() if capa_ids else []
    related_audit_findings = db.query(AuditFinding).filter(AuditFinding.id.in_(list(audit_ids))).all() if audit_ids else []
    related_decisions = db.query(Decision).filter(Decision.id.in_(list(decision_ids))).all() if decision_ids else []

    return {
        "sop": _build_sop_dict(sop, include_current_version=True, db=db),
        "related_sops": related_sops,
        "related_deviations": related_deviations,
        "related_capas": related_capas,
        "related_audit_findings": related_audit_findings,
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


@router.get("/api/deviations/{id}/context", response_model=DeviationContextResponse)
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
    return _tenant_scoped_query(db, Deviation).all()

@router.post("/api/deviations", response_model=DeviationResponse)
def create_deviation(payload: DeviationCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Create a new Deviation record."""
    dev = Deviation(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "deviation", dev.id)
    return dev

@router.put("/api/deviations/{id}", response_model=DeviationResponse)
def update_deviation(id: str, payload: DeviationCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Update an existing Deviation record."""
    dev = db.query(Deviation).filter(Deviation.id == id, Deviation.tenant_id == FIXED_TENANT_ID).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found")
    
    for key, value in payload.model_dump().items():
        setattr(dev, key, value)
    
    db.commit()
    db.refresh(dev)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "deviation", dev.id)
    return dev

# ==========================================
# CAPA ROUTES
# ==========================================

@router.get("/api/capas", response_model=List[CapaResponse])
def get_all_capas(db: Session = Depends(get_db)):
    """Return all CAPA records."""
    return _tenant_scoped_query(db, Capa).all()

@router.post("/api/capas", response_model=CapaResponse)
def create_capa(payload: CapaCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Create a new CAPA record."""
    capa = Capa(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(capa)
    db.commit()
    db.refresh(capa)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "capa", capa.id)
    return capa

@router.get("/api/capas/{id}", response_model=CapaResponse)
def get_capa(id: str, db: Session = Depends(get_db)):
    """Return a single CAPA record."""
    capa = db.query(Capa).filter(Capa.id == id, Capa.tenant_id == FIXED_TENANT_ID).first()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    return capa

@router.put("/api/capas/{id}", response_model=CapaResponse)
def update_capa(id: str, payload: CapaCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Update an existing CAPA record."""
    capa = db.query(Capa).filter(Capa.id == id, Capa.tenant_id == FIXED_TENANT_ID).first()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    
    for key, value in payload.model_dump().items():
        setattr(capa, key, value)
    
    db.commit()
    db.refresh(capa)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "capa", capa.id)
    return capa

# ==========================================
# AUDIT ROUTES
# ==========================================

@router.get("/api/audits", response_model=List[AuditFindingResponse])
def get_all_audits(db: Session = Depends(get_db)):
    """Return all Audit Finding records."""
    return _tenant_scoped_query(db, AuditFinding).all()

@router.post("/api/audits", response_model=AuditFindingResponse)
def create_audit(payload: AuditFindingCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Create a new Audit Finding record."""
    audit = AuditFinding(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "audit_finding", audit.id)
    return audit

@router.get("/api/audits/{id}", response_model=AuditFindingResponse)
def get_audit(id: str, db: Session = Depends(get_db)):
    """Return a single Audit Finding record."""
    audit = db.query(AuditFinding).filter(AuditFinding.id == id, AuditFinding.tenant_id == FIXED_TENANT_ID).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit Finding not found")
    return audit

@router.put("/api/audits/{id}", response_model=AuditFindingResponse)
def update_audit(id: str, payload: AuditFindingCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Update an existing Audit Finding record."""
    audit = db.query(AuditFinding).filter(AuditFinding.id == id, AuditFinding.tenant_id == FIXED_TENANT_ID).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit Finding not found")
    
    for key, value in payload.model_dump().items():
        setattr(audit, key, value)
    
    db.commit()
    db.refresh(audit)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "audit_finding", audit.id)
    return audit

# ==========================================
# DECISION ROUTES
# ==========================================

@router.get("/api/decisions", response_model=List[DecisionResponse])
def get_all_decisions(db: Session = Depends(get_db)):
    """Return all Decision records."""
    return _tenant_scoped_query(db, Decision).all()

@router.post("/api/decisions", response_model=DecisionResponse)
def create_decision(payload: DecisionCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Create a new Decision record."""
    decision = Decision(
        tenant_id=FIXED_TENANT_ID,
        **payload.model_dump()
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "decision", decision.id)
    return decision

@router.get("/api/decisions/{id}", response_model=DecisionResponse)
def get_decision(id: str, db: Session = Depends(get_db)):
    """Return a single Decision record."""
    decision = db.query(Decision).filter(Decision.id == id, Decision.tenant_id == FIXED_TENANT_ID).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision

@router.put("/api/decisions/{id}", response_model=DecisionResponse)
def update_decision(id: str, payload: DecisionCreateUpdate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Update an existing Decision record."""
    decision = db.query(Decision).filter(Decision.id == id, Decision.tenant_id == FIXED_TENANT_ID).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    for key, value in payload.model_dump().items():
        setattr(decision, key, value)
    
    db.commit()
    db.refresh(decision)
    if background_tasks:
        _schedule_semantic_job(background_tasks, "decision", decision.id)
    return decision

# ==========================================
# DATASET IMPORT ROUTE
# ==========================================

@router.post("/api/import/dataset")
def import_dataset(payload: DatasetImportRequest, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """
    Import a dataset of entities (SOPs, Deviations, CAPAs, Audit Findings, Decisions, and Links).
    Transactional and supports nested batches for bulk ingestion.
    """
    try:
        default_tenant = uuid.UUID("11111111-1111-1111-1111-111111111111")
        counts = {"sops": 0, "deviations": 0, "capas": 0, "audits": 0, "decisions": 0, "links": 0, "failed_links": 0}
        reindex_entities: set[tuple[str, uuid.UUID]] = set()

        all_links = []

        def find_existing(model, *, entity_id=None, external_id=None, lookup_field=None, lookup_value=None):
            if entity_id:
                existing = db.query(model).filter(model.id == entity_id).first()
                if existing:
                    return existing
            if external_id:
                existing = db.query(model).filter(model.external_id == external_id).first()
                if existing:
                    return existing
            if lookup_field and lookup_value:
                existing = db.query(model).filter(getattr(model, lookup_field) == lookup_value).first()
                if existing:
                    return existing
            return None

        def resolve_link_entity(model, entity_id=None, external_id=None):
            if entity_id:
                try:
                    parsed_id = uuid.UUID(str(entity_id))
                    existing = db.query(model).filter(model.id == parsed_id).first()
                    if existing:
                        return existing
                except Exception:
                    pass
            if external_id:
                return db.query(model).filter(model.external_id == external_id).first()
            return None

        for batch in payload.entities:
            # Normalize batch keys
            batch_sops = batch.get("sops", [])
            batch_deviations = batch.get("deviations", [])
            batch_capas = batch.get("capas", [])
            batch_audits = batch.get("audit_findings", []) or batch.get("audits", [])
            batch_decisions = batch.get("decisions", [])
            
            # 1. SOPs
            for s in batch_sops:
                sop_id = uuid.UUID(s["id"]) if s.get("id") else None
                sop = find_existing(
                    SOP,
                    entity_id=sop_id,
                    external_id=s.get("external_id"),
                    lookup_field="sop_number",
                    lookup_value=s.get("sop_number"),
                )
                if not sop:
                    sop_id = sop_id or uuid.uuid4()
                    sop = SOP(
                        id=sop_id,
                        tenant_id=uuid.UUID(s.get("tenant_id")) if s.get("tenant_id") else default_tenant,
                        external_id=s.get("external_id"),
                        sop_number=s.get("sop_number", "SOP-NEW"),
                        title=s.get("title", "Untitled SOP"),
                        department=s.get("department", "Quality"),
                        source_system=s.get("source_system", "import"),
                        is_active=s.get("is_active", True)
                    )
                    db.add(sop)
                    counts["sops"] += 1
                else:
                    sop_id = sop.id
                    if s.get("external_id") and not sop.external_id:
                        sop.external_id = s.get("external_id")
                reindex_entities.add(("sop", sop_id))
                
                # Add Initial Version if provided
                if s.get("versions"):
                    for v in s.get("versions"):
                        v_id = uuid.UUID(v["id"]) if v.get("id") else uuid.uuid4()
                        existing_v = db.query(SOPVersion).filter(SOPVersion.id == v_id).first()
                        if not existing_v:
                            new_v = SOPVersion(
                                id=v_id,
                                sop_id=sop_id,
                                version_number=v.get("version_number", "1"),
                                external_status=v.get("external_status", "effective"),
                                content_json=v.get("content_json", {"type": "doc", "content": []}),
                                metadata_json=v.get("metadata_json", {}),
                                effective_date=v.get("effective_date"),
                                review_date=v.get("review_date")
                            )
                            db.add(new_v)
                            if v.get("is_current") or not sop.current_version_id:
                                sop.current_version_id = v_id
            
            # 2. Deviations
            for d in batch_deviations:
                d_id = uuid.UUID(d["id"]) if d.get("id") else None
                dev = find_existing(
                    Deviation,
                    entity_id=d_id,
                    external_id=d.get("external_id"),
                    lookup_field="deviation_number",
                    lookup_value=d.get("deviation_number"),
                )
                if not dev:
                    d_id = d_id or uuid.uuid4()
                    dev = Deviation(
                        id=d_id,
                        tenant_id=uuid.UUID(d.get("tenant_id")) if d.get("tenant_id") else default_tenant,
                        external_id=d.get("external_id"),
                        deviation_number=d.get("deviation_number", "DEV-NEW"),
                        title=d.get("title", "Untitled Deviation"),
                        category=d.get("category"),
                        site=d.get("site"),
                        product_line=d.get("product_line"),
                        external_status=d.get("external_status", "open"),
                        description_text=d.get("description_text"),
                        root_cause_text=d.get("root_cause_text"),
                        impact_level=d.get("impact_level"),
                        source_system=d.get("source_system", "import")
                    )
                    db.add(dev)
                    counts["deviations"] += 1
                elif d.get("external_id") and not dev.external_id:
                    dev.external_id = d.get("external_id")
                reindex_entities.add(("deviation", dev.id))

            # 3. CAPAs
            for c in batch_capas:
                c_id = uuid.UUID(c["id"]) if c.get("id") else None
                capa = find_existing(
                    Capa,
                    entity_id=c_id,
                    external_id=c.get("external_id"),
                    lookup_field="capa_number",
                    lookup_value=c.get("capa_number"),
                )
                if not capa:
                    c_id = c_id or uuid.uuid4()
                    capa = Capa(
                        id=c_id,
                        tenant_id=uuid.UUID(c.get("tenant_id")) if c.get("tenant_id") else default_tenant,
                        external_id=c.get("external_id"),
                        capa_number=c.get("capa_number", "CAPA-NEW"),
                        title=c.get("title", "Untitled CAPA"),
                        external_status=c.get("external_status", "open"),
                        action_type=c.get("action_type"),
                        action_text=c.get("action_text"),
                        owner_name=c.get("owner_name"),
                        source_system=c.get("source_system", "import")
                    )
                    db.add(capa)
                    counts["capas"] += 1
                elif c.get("external_id") and not capa.external_id:
                    capa.external_id = c.get("external_id")
                reindex_entities.add(("capa", capa.id))

            # 4. Audit Findings
            for a in batch_audits:
                a_id = uuid.UUID(a["id"]) if a.get("id") else None
                audit = find_existing(
                    AuditFinding,
                    entity_id=a_id,
                    external_id=a.get("external_id"),
                    lookup_field="finding_number",
                    lookup_value=a.get("finding_number") or a.get("audit_number"),
                )
                if not audit:
                    a_id = a_id or uuid.uuid4()
                    audit = AuditFinding(
                        id=a_id,
                        tenant_id=uuid.UUID(a.get("tenant_id")) if a.get("tenant_id") else default_tenant,
                        external_id=a.get("external_id"),
                        audit_number=a.get("audit_number"),
                        finding_number=a.get("finding_number"),
                        authority=a.get("authority"),
                        question_text=a.get("question_text"),
                        finding_text=a.get("finding_text"),
                        acceptance_status=a.get("acceptance_status", "pending"),
                        source_system=a.get("source_system", "import")
                    )
                    db.add(audit)
                    counts["audits"] += 1
                elif a.get("external_id") and not audit.external_id:
                    audit.external_id = a.get("external_id")
                reindex_entities.add(("audit_finding", audit.id))

            # 5. Decisions
            for dec in batch_decisions:
                dec_id = uuid.UUID(dec["id"]) if dec.get("id") else None
                decision = find_existing(
                    Decision,
                    entity_id=dec_id,
                    external_id=dec.get("external_id"),
                    lookup_field="decision_number",
                    lookup_value=dec.get("decision_number") or dec.get("title"),
                )
                if not decision:
                    dec_id = dec_id or uuid.uuid4()
                    decision = Decision(
                        id=dec_id,
                        tenant_id=uuid.UUID(dec.get("tenant_id")) if dec.get("tenant_id") else default_tenant,
                        external_id=dec.get("external_id"),
                        decision_number=dec.get("decision_number"),
                        title=dec.get("title", "Untitled Decision"),
                        decision_statement=dec.get("decision_statement", "No statement"),
                        source_system=dec.get("source_system", "import")
                    )
                    db.add(decision)
                    counts["decisions"] += 1
                elif dec.get("external_id") and not decision.external_id:
                    decision.external_id = dec.get("external_id")
                reindex_entities.add(("decision", decision.id))

            # Accumulate Links for after flush
            all_links.extend(batch.get("links", []))

        # Flush entity creations to Database to establish valid primary keys
        db.flush()

        # 6. Process Links (with Validation)
        for l in all_links:
            l_type = (l.get("link_type") or l.get("type", "")).lower()
            source_id = l.get("source_id")
            target_id = l.get("target_id")
            source_external_id = l.get("source_external_id")
            target_external_id = l.get("target_external_id")
            
            if l_type == "sop-deviation":
                source = resolve_link_entity(SOP, entity_id=source_id, external_id=source_external_id)
                target = resolve_link_entity(Deviation, entity_id=target_id, external_id=target_external_id)
                if source and target:
                    if not db.query(SopDeviationLink).filter(SopDeviationLink.sop_id == source.id, SopDeviationLink.deviation_id == target.id).first():
                        db.add(SopDeviationLink(id=uuid.uuid4(), tenant_id=default_tenant, sop_id=source.id, deviation_id=target.id))
                        counts["links"] += 1
                else:
                    counts["failed_links"] += 1
            elif l_type == "deviation-capa":
                source = resolve_link_entity(Deviation, entity_id=source_id, external_id=source_external_id)
                target = resolve_link_entity(Capa, entity_id=target_id, external_id=target_external_id)
                if source and target:
                    if not db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id == source.id, DeviationCapaLink.capa_id == target.id).first():
                        db.add(DeviationCapaLink(id=uuid.uuid4(), tenant_id=default_tenant, deviation_id=source.id, capa_id=target.id))
                        counts["links"] += 1
                else:
                    counts["failed_links"] += 1
            elif l_type == "capa-audit":
                source = resolve_link_entity(Capa, entity_id=source_id, external_id=source_external_id)
                target = resolve_link_entity(AuditFinding, entity_id=target_id, external_id=target_external_id)
                if source and target:
                    if not db.query(CapaAuditLink).filter(CapaAuditLink.capa_id == source.id, CapaAuditLink.audit_finding_id == target.id).first():
                        db.add(CapaAuditLink(id=uuid.uuid4(), tenant_id=default_tenant, capa_id=source.id, audit_finding_id=target.id))
                        counts["links"] += 1
                else:
                    counts["failed_links"] += 1
            elif l_type == "audit-decision":
                source = resolve_link_entity(AuditFinding, entity_id=source_id, external_id=source_external_id)
                target = resolve_link_entity(Decision, entity_id=target_id, external_id=target_external_id)
                if source and target:
                    if not db.query(AuditDecisionLink).filter(AuditDecisionLink.audit_finding_id == source.id, AuditDecisionLink.decision_id == target.id).first():
                        db.add(AuditDecisionLink(id=uuid.uuid4(), tenant_id=default_tenant, audit_finding_id=source.id, decision_id=target.id))
                        counts["links"] += 1
                else:
                    counts["failed_links"] += 1
            elif l_type == "decision-sop":
                source = resolve_link_entity(Decision, entity_id=source_id, external_id=source_external_id)
                target = resolve_link_entity(SOP, entity_id=target_id, external_id=target_external_id)
                if source and target:
                    if not db.query(DecisionSopLink).filter(DecisionSopLink.decision_id == source.id, DecisionSopLink.sop_id == target.id).first():
                        db.add(DecisionSopLink(id=uuid.uuid4(), tenant_id=default_tenant, decision_id=source.id, sop_id=target.id))
                        counts["links"] += 1
                else:
                    counts["failed_links"] += 1
            else:
                counts["failed_links"] += 1

        db.commit()
        if background_tasks:
            for et, eid in reindex_entities:
                _schedule_semantic_job(background_tasks, et, eid, job_type="import_reindex")
        return {
            "message": "Import successful",
            "stats": counts
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# ==========================================
# SEARCH & STATS AGGREGATION ROUTES
# ==========================================

@router.get("/api/stats")
def get_knowledge_stats(db: Session = Depends(get_db)):
    """Return total counts of all entities in the tenant."""
    return {
        "sops": _tenant_scoped_query(db, SOP).count(),
        "deviations": _tenant_scoped_query(db, Deviation).count(),
        "capas": _tenant_scoped_query(db, Capa).count(),
        "audits": _tenant_scoped_query(db, AuditFinding).count(),
        "decisions": _tenant_scoped_query(db, Decision).count()
    }


@router.get("/api/search")
def search_knowledge(q: str, db: Session = Depends(get_db)):
    """
    Search across all knowledge entities (SOP, Deviation, Capa, Audit, Decision).
    Maps into structured cards for the UI renderer.
    """
    query = f"%{q}%"
    results = []

    # SOPs
    sops = _tenant_scoped_query(db, SOP).filter(
        or_(
            SOP.title.ilike(query),
            SOP.sop_number.ilike(query),
            SOP.department.ilike(query)
        )
    ).all()
    
    for sop in sops:
        has_content = bool(sop.current_version_id)
        results.append({
            "id": str(sop.id),
            "type": "sop",
            "typeLabel": "SOP",
            "metadata": f"{sop.sop_number or ''} · {sop.department or 'Allgemein'}",
            "matchPercent": 95,
            "title": sop.title or "Ohne Titel",
            "excerpt": "SOP Inhalt für KI Kontext indexiert..." if has_content else "Kein Inhalt verfügbar.",
            "badges": [
                {"label": "Aktiv" if sop.is_active else "Inaktiv", "color": "green" if sop.is_active else "gray"}
            ],
            "sourceIcon": "📄",
            "sourceColorClass": "source-sop"
        })

    # Deviations
    devs = _tenant_scoped_query(db, Deviation).filter(
        or_(
            Deviation.title.ilike(query),
            Deviation.deviation_number.ilike(query),
            Deviation.description_text.ilike(query)
        )
    ).all()

    for dev in devs:
        desc = dev.description_text or "Keine Beschreibung"
        results.append({
            "id": str(dev.id),
            "type": "deviation",
            "typeLabel": "Abweichung",
            "metadata": f"{dev.deviation_number or ''} · {dev.site or 'Allgemein'}",
            "matchPercent": 88,
            "title": dev.title or "Unbekannte Abweichung",
            "excerpt": (desc[:140] + '...') if len(desc) > 140 else desc,
            "badges": [
                {"label": dev.external_status or "Offen", "color": "green" if getattr(dev, 'external_status', '') == "closed" else "orange"},
                {"label": dev.impact_level or "Normal", "color": "red" if dev.impact_level == "high" else "gray"}
            ],
            "sourceIcon": "⚠",
            "sourceColorClass": "source-warning"
        })

    # CAPAs
    capas = _tenant_scoped_query(db, Capa).filter(
        or_(
            Capa.title.ilike(query),
            Capa.capa_number.ilike(query),
            Capa.action_text.ilike(query)
        )
    ).all()
    
    for capa in capas:
        desc = capa.action_text or "Keine Beschreibung"
        results.append({
            "id": str(capa.id),
            "type": "capa",
            "typeLabel": "CAPA",
            "metadata": f"{capa.capa_number or ''}",
            "matchPercent": 85,
            "title": capa.title or "Unbekannte CAPA",
            "excerpt": (desc[:140] + '...') if len(desc) > 140 else desc,
            "badges": [
                {"label": capa.external_status or "Offen", "color": "green" if getattr(capa, 'external_status', '') == "closed" else "orange"}
            ],
            "sourceIcon": "◆",
            "sourceColorClass": "source-warning"
        })

    # Audits
    audits = _tenant_scoped_query(db, AuditFinding).filter(
        or_(
            AuditFinding.finding_number.ilike(query),
            AuditFinding.finding_text.ilike(query),
            AuditFinding.question_text.ilike(query)
        )
    ).all()
    
    for aud in audits:
        desc = aud.finding_text or aud.question_text or "Keine Beschreibung"
        results.append({
            "id": str(aud.id),
            "type": "audit",
            "typeLabel": "Audit Finding",
            "metadata": f"{aud.finding_number or ''}",
            "matchPercent": 82,
            "title": aud.finding_number or "Unbekanntes Finding",
            "excerpt": (desc[:140] + '...') if len(desc) > 140 else desc,
            "badges": [
                {"label": aud.acceptance_status or 'Minor', "color": "blue"}
            ],
            "sourceIcon": "✓",
            "sourceColorClass": "source-audit"
        })

    # Decisions
    is_decision_query = q.lower() in ["decision", "decisions", "entscheidung", "entscheidungen"]
    decisions = _tenant_scoped_query(db, Decision).filter(
        or_(
            Decision.title.ilike(query),
            Decision.decision_number.ilike(query),
            Decision.decision_type.ilike(query),
            Decision.decision_statement.ilike(query),
            Decision.rationale_text.ilike(query),
            Decision.risk_assessment_text.ilike(query),
            Decision.final_conclusion.ilike(query),
            True if is_decision_query else False
        )
    ).all()
    
    for dec in decisions:
        desc = dec.decision_statement or dec.rationale_text or "Keine Beschreibung"
        results.append({
            "id": str(dec.id),
            "type": "decision",
            "typeLabel": "Decision",
            "metadata": f"{dec.decision_number or ''} · {dec.decision_type or 'Allgemein'}",
            "matchPercent": 80,
            "title": dec.title or dec.decision_number or "Unbekannte Entscheidung",
            "excerpt": (desc[:140] + '...') if len(desc) > 140 else desc,
            "badges": [],
            "sourceIcon": "❓",
            "sourceColorClass": "source-decision"
        })

    # Sort logic mimicking the frontend
    results.sort(key=lambda x: x["matchPercent"], reverse=True)
    
    return results

# ==========================================
# MANUAL LINKING ROUTES
# ==========================================

@router.post("/api/links")
def create_link(payload: LinkRequest, db: Session = Depends(get_db)):
    """Create a manual link between two entities."""
    l_type = payload.link_type.lower()
    source_id = payload.source_id
    target_id = payload.target_id
    
    link_obj = None
    if l_type == "sop-deviation":
        link_obj = SopDeviationLink(id=uuid.uuid4(), tenant_id=FIXED_TENANT_ID, sop_id=source_id, deviation_id=target_id, rationale_text=payload.rationale_text)
    elif l_type == "deviation-capa":
        link_obj = DeviationCapaLink(id=uuid.uuid4(), tenant_id=FIXED_TENANT_ID, deviation_id=source_id, capa_id=target_id, rationale_text=payload.rationale_text)
    elif l_type == "capa-audit":
        link_obj = CapaAuditLink(id=uuid.uuid4(), tenant_id=FIXED_TENANT_ID, capa_id=source_id, audit_finding_id=target_id, rationale_text=payload.rationale_text)
    elif l_type == "audit-decision":
        link_obj = AuditDecisionLink(id=uuid.uuid4(), tenant_id=FIXED_TENANT_ID, audit_finding_id=source_id, decision_id=target_id, rationale_text=payload.rationale_text)
    elif l_type == "decision-sop":
        link_obj = DecisionSopLink(id=uuid.uuid4(), tenant_id=FIXED_TENANT_ID, decision_id=source_id, sop_id=target_id, rationale_text=payload.rationale_text)
    
    if not link_obj:
        raise HTTPException(status_code=400, detail=f"Unsupported link type: {l_type}")
        
    db.add(link_obj)
    db.commit()
    return {"status": "success", "link_id": str(link_obj.id)}

@router.delete("/api/links/{link_type}/{link_id}")
def delete_link(link_type: str, link_id: UUID, db: Session = Depends(get_db)):
    """Delete a manual link."""
    l_type = link_type.lower()
    
    model_map = {
        "sop-deviation": SopDeviationLink,
        "deviation-capa": DeviationCapaLink,
        "capa-audit": CapaAuditLink,
        "audit-decision": AuditDecisionLink,
        "decision-sop": DecisionSopLink
    }
    
    if l_type not in model_map:
        raise HTTPException(status_code=400, detail=f"Unsupported link type: {l_type}")
        
    link = db.query(model_map[l_type]).filter(model_map[l_type].id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
        
    db.delete(link)
    db.commit()
    return {"status": "success"}

# ==========================================
# NORMALIZATION & BGE-M3 PREP (PLACEHOLDERS)
# ==========================================

@router.post("/api/normalization/unified-ingest")
def unified_ingest(payload: dict, db: Session = Depends(get_db)):
    """
    Placeholder for the unified normalization flow.
    Ensures all ingested content (Editor or Upload) follows one pipe.
    """
    return {"status": "stub", "message": "Normalization service ready for integration"}

@router.post("/api/semantic/reindex")
def semantic_reindex(
    payload: SemanticReindexRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Queue semantic reindex jobs (delta or full) for BGE-M3 + Qdrant indexing.
    """
    queued = []
    if payload.full_reindex:
        for sop in _tenant_scoped_query(db, SOP).all():
            _schedule_semantic_job(background_tasks, "sop", sop.id, sop.current_version_id, "full_reindex")
            queued.append({"entity_type": "sop", "entity_id": str(sop.id)})
        for dev in _tenant_scoped_query(db, Deviation).all():
            _schedule_semantic_job(background_tasks, "deviation", dev.id, None, "full_reindex")
            queued.append({"entity_type": "deviation", "entity_id": str(dev.id)})
        for capa in _tenant_scoped_query(db, Capa).all():
            _schedule_semantic_job(background_tasks, "capa", capa.id, None, "full_reindex")
            queued.append({"entity_type": "capa", "entity_id": str(capa.id)})
        for audit in _tenant_scoped_query(db, AuditFinding).all():
            _schedule_semantic_job(background_tasks, "audit_finding", audit.id, None, "full_reindex")
            queued.append({"entity_type": "audit_finding", "entity_id": str(audit.id)})
        for decision in _tenant_scoped_query(db, Decision).all():
            _schedule_semantic_job(background_tasks, "decision", decision.id, None, "full_reindex")
            queued.append({"entity_type": "decision", "entity_id": str(decision.id)})
    else:
        if not payload.entity_type or not payload.entity_id:
            raise HTTPException(status_code=422, detail="entity_type and entity_id are required unless full_reindex=true.")
        normalized_type = payload.entity_type.strip().lower()
        if normalized_type not in ENTITY_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported entity_type '{payload.entity_type}'.")
        _schedule_semantic_job(background_tasks, normalized_type, payload.entity_id, payload.version_id, "manual_reindex")
        queued.append({"entity_type": normalized_type, "entity_id": str(payload.entity_id)})

    return {
        "status": "queued",
        "count": len(queued),
        "jobs": queued,
    }


@router.get("/api/semantic/suggestions", response_model=list[LinkSuggestionResponse])
def get_semantic_suggestions(
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    normalized_type = entity_type.strip().lower()
    if normalized_type not in ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported entity_type '{entity_type}'.")
    return (
        db.query(AILinkSuggestion)
        .filter(
            AILinkSuggestion.source_entity_type == normalized_type,
            AILinkSuggestion.source_entity_id == entity_id,
        )
        .order_by(AILinkSuggestion.score.desc(), AILinkSuggestion.created_at.desc())
        .all()
    )


@router.post("/api/semantic/suggestions/{suggestion_id}/accept")
def accept_semantic_suggestion(suggestion_id: UUID, approved_by: str | None = None, db: Session = Depends(get_db)):
    suggestion = db.query(AILinkSuggestion).filter(AILinkSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    SemanticPipelineService.accept_suggestion(db, suggestion, approved_by=approved_by)
    return {"status": "accepted", "id": str(suggestion_id)}


@router.post("/api/semantic/suggestions/{suggestion_id}/reject")
def reject_semantic_suggestion(suggestion_id: UUID, approved_by: str | None = None, db: Session = Depends(get_db)):
    suggestion = db.query(AILinkSuggestion).filter(AILinkSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    SemanticPipelineService.reject_suggestion(db, suggestion, approved_by=approved_by)
    return {"status": "rejected", "id": str(suggestion_id)}


@router.get("/api/semantic/status", response_model=SemanticStatusResponse)
def get_semantic_status(entity_type: str = Query(...), entity_id: UUID = Query(...), db: Session = Depends(get_db)):
    normalized_type = entity_type.strip().lower()
    if normalized_type not in ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported entity_type '{entity_type}'.")
    return SemanticPipelineService.get_entity_status(db, normalized_type, entity_id)
