from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from .models import Document, DocumentVersion
from .schemas import (
    CreateDocumentRequest,
    UpdateDocumentRequest,
    CreateVersionRequest,
    UpdateVersionStatusRequest,
)

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/api/editor/docs")
def create_document(payload: CreateDocumentRequest, db: Session = Depends(get_db)):
    doc = Document(
        title=payload.title,
        profile=payload.profile,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    initial_version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        doc_json={"type": "doc", "content": []},
        change_summary="Initial version",
        status="draft",
        metadata_json={}
    )
    db.add(initial_version)
    db.commit()
    db.refresh(initial_version)

    doc.current_version_id = initial_version.id
    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "title": doc.title,
        "profile": doc.profile,
        "current_version_id": str(doc.current_version_id),
    }


@router.get("/api/editor/docs/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = db.query(DocumentVersion).filter(DocumentVersion.id == doc.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found")

    return {
        "id": str(doc.id),
        "title": doc.title,
        "profile": doc.profile,
        "current_version_id": str(doc.current_version_id),
        "current_version": {
            "id": str(current_version.id),
            "document_id": str(current_version.document_id),
            "version_number": current_version.version_number,
            "doc_json": current_version.doc_json,
            "change_summary": current_version.change_summary,
            "status": current_version.status,
            "metadata_json": current_version.metadata_json,
            "created_at": current_version.created_at,
        }
    }


@router.put("/api/editor/docs/{doc_id}")
def update_document(doc_id: str, payload: UpdateDocumentRequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = db.query(DocumentVersion).filter(DocumentVersion.id == doc.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=404, detail="Current version not found")

    current_version.doc_json = payload.doc_json
    current_version.metadata_json = payload.metadata_json or current_version.metadata_json
    db.commit()
    db.refresh(current_version)

    return {"message": "Document updated", "current_version_id": str(current_version.id)}


@router.get("/api/editor/docs/{doc_id}/versions")
def list_versions(doc_id: str, db: Session = Depends(get_db)):
    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc_id)
        .order_by(DocumentVersion.version_number.asc())
        .all()
    )

    return [
        {
            "id": str(v.id),
            "document_id": str(v.document_id),
            "version_number": v.version_number,
            "status": v.status,
            "change_summary": v.change_summary,
            "metadata_json": v.metadata_json,
            "created_at": v.created_at,
        }
        for v in versions
    ]


@router.post("/api/editor/docs/{doc_id}/versions")
def create_version(doc_id: str, payload: CreateVersionRequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    max_version = db.query(func.max(DocumentVersion.version_number)).filter(DocumentVersion.document_id == doc_id).scalar()
    next_version = (max_version or 0) + 1

    version = DocumentVersion(
        document_id=doc.id,
        version_number=next_version,
        doc_json=payload.doc_json,
        change_summary=payload.change_summary,
        status="draft",
        metadata_json=payload.metadata_json or {},
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    doc.current_version_id = version.id
    db.commit()

    return {
        "id": str(version.id),
        "document_id": str(version.document_id),
        "version_number": version.version_number,
        "status": version.status,
    }


@router.get("/api/editor/docs/{doc_id}/versions/{version_id}")
def get_version(doc_id: str, version_id: str, db: Session = Depends(get_db)):
    version = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc_id, DocumentVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return {
        "id": str(version.id),
        "document_id": str(version.document_id),
        "version_number": version.version_number,
        "doc_json": version.doc_json,
        "change_summary": version.change_summary,
        "status": version.status,
        "metadata_json": version.metadata_json,
        "created_at": version.created_at,
    }


@router.put("/api/editor/docs/{doc_id}/versions/{version_id}/status")
def update_version_status(doc_id: str, version_id: str, payload: UpdateVersionStatusRequest, db: Session = Depends(get_db)):
    version = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc_id, DocumentVersion.id == version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    version.status = payload.status
    if payload.metadata_json is not None:
        version.metadata_json = payload.metadata_json

    db.commit()
    db.refresh(version)

    return {
        "message": "Version status updated",
        "id": str(version.id),
        "status": version.status,
    }
