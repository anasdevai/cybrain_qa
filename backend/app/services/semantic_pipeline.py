import os
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import (
    AILinkSuggestion,
    AuditDecisionLink,
    AuditFinding,
    Capa,
    CapaAuditLink,
    Decision,
    DecisionSopLink,
    Deviation,
    DeviationCapaLink,
    EmbeddingJob,
    KnowledgeChunk,
    SOP,
    SOPVersion,
    SopDeviationLink,
)

BGE_M3_MODEL = "BAAI/bge-m3"
DEFAULT_COLLECTION = os.getenv("SEMANTIC_QDRANT_COLLECTION", "qa_semantic_chunks")
ENTITY_TYPES = {"sop", "deviation", "capa", "audit_finding", "decision"}
LINK_RULES = {
    "sop": ("deviation", "sop-deviation", 0.63),
    "deviation": ("capa", "deviation-capa", 0.62),
    "capa": ("audit_finding", "capa-audit", 0.62),
    "audit_finding": ("decision", "audit-decision", 0.6),
    "decision": ("sop", "decision-sop", 0.64),
}

_embedder: SentenceTransformer | None = None
_qdrant: QdrantClient | None = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(BGE_M3_MODEL, device=os.getenv("EMBEDDING_DEVICE", "cpu"))
    return _embedder


def _get_qdrant() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        qdrant_url = os.getenv("QDRANT_URL")
        if not qdrant_url:
            raise RuntimeError("QDRANT_URL is not configured.")
        _qdrant = QdrantClient(url=qdrant_url, api_key=os.getenv("QDRANT_API_KEY"))
    return _qdrant


def _split_long_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def _extract_tiptap_sections(content_json: dict[str, Any] | None) -> list[tuple[str, str]]:
    if not isinstance(content_json, dict):
        return []
    current_section = "General"
    sections: dict[str, list[str]] = defaultdict(list)
    for node in content_json.get("content", []) or []:
        ntype = node.get("type")
        if ntype == "heading":
            texts = []
            for c in node.get("content", []) or []:
                if c.get("type") == "text" and c.get("text"):
                    texts.append(c["text"])
            heading = " ".join(texts).strip()
            if heading:
                current_section = heading
            continue
        texts = []
        for c in node.get("content", []) or []:
            if c.get("type") == "text" and c.get("text"):
                texts.append(c["text"])
        txt = " ".join(texts).strip()
        if txt:
            sections[current_section].append(txt)
    return [(name, "\n".join(lines).strip()) for name, lines in sections.items() if lines]


class SemanticPipelineService:
    @staticmethod
    def enqueue_reindex(entity_type: str, entity_id: uuid.UUID, version_id: uuid.UUID | None = None, job_type: str = "entity_reindex") -> uuid.UUID:
        db = SessionLocal()
        try:
            job = EmbeddingJob(
                entity_type=entity_type,
                entity_id=entity_id,
                version_id=version_id,
                job_type=job_type,
                status="pending",
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job.id
        finally:
            db.close()

    @staticmethod
    def process_job(job_id: uuid.UUID):
        db = SessionLocal()
        try:
            job = db.query(EmbeddingJob).filter(EmbeddingJob.id == job_id).first()
            if not job:
                return
            job.status = "running"
            job.started_at = datetime.utcnow()
            db.commit()

            SemanticPipelineService._index_entity(db, job.entity_type, job.entity_id, job.version_id)
            SemanticPipelineService._generate_suggestions(db, job.entity_type, job.entity_id)

            job.status = "completed"
            job.finished_at = datetime.utcnow()
            job.error_message = None
            db.commit()
        except Exception as exc:
            if "job" in locals() and job:
                job.status = "failed"
                job.finished_at = datetime.utcnow()
                job.error_message = str(exc)[:2000]
                db.commit()
            raise
        finally:
            db.close()

    @staticmethod
    def _ensure_collection(dim: int):
        client = _get_qdrant()
        if not client.collection_exists(DEFAULT_COLLECTION):
            client.create_collection(
                collection_name=DEFAULT_COLLECTION,
                vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
            )
        # Cloud Qdrant can require payload indexes for filtered query performance/validity.
        try:
            client.create_payload_index(
                collection_name=DEFAULT_COLLECTION,
                field_name="entity_type",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            # Index may already exist; keep indexing flow idempotent.
            pass

    @staticmethod
    def _normalize_entity(db: Session, entity_type: str, entity_id: uuid.UUID, version_id: uuid.UUID | None):
        if entity_type == "sop":
            sop = db.query(SOP).filter(SOP.id == entity_id).first()
            if not sop:
                return [], None
            version = None
            if version_id:
                version = db.query(SOPVersion).filter(SOPVersion.id == version_id, SOPVersion.sop_id == sop.id).first()
            if not version:
                version = db.query(SOPVersion).filter(SOPVersion.id == sop.current_version_id).first() if sop.current_version_id else None
            if not version:
                return [], None
            meta = version.metadata_json or {}
            sop_meta = meta.get("sopMetadata", {}) if isinstance(meta, dict) else {}
            sections = _extract_tiptap_sections(version.content_json if isinstance(version.content_json, dict) else {})
            if not sections:
                normalized = "\n".join(
                    [
                        f"title: {sop.title or ''}",
                        f"purpose: {sop_meta.get('purpose', '')}",
                        f"scope: {sop_meta.get('scope', '')}",
                        f"responsibilities: {sop_meta.get('responsibilities', '')}",
                        f"procedure: {sop_meta.get('procedure', '')}",
                        f"documentation: {sop_meta.get('documentation', '')}",
                    ]
                ).strip()
                sections = [("General", normalized)]
            return sections, version.id

        if entity_type == "deviation":
            row = db.query(Deviation).filter(Deviation.id == entity_id).first()
            if not row:
                return [], None
            text = "\n".join(
                [
                    f"title: {row.title or ''}",
                    f"description: {row.description_text or ''}",
                    f"root_cause: {row.root_cause_text or ''}",
                    f"category: {row.category or ''}",
                    f"impact_level: {row.impact_level or ''}",
                ]
            ).strip()
            return [("Deviation", text)], None

        if entity_type == "capa":
            row = db.query(Capa).filter(Capa.id == entity_id).first()
            if not row:
                return [], None
            text = "\n".join(
                [
                    f"title: {row.title or ''}",
                    f"action: {row.action_text or ''}",
                    f"effectiveness: {row.effectiveness_text or ''}",
                ]
            ).strip()
            return [("CAPA", text)], None

        if entity_type == "audit_finding":
            row = db.query(AuditFinding).filter(AuditFinding.id == entity_id).first()
            if not row:
                return [], None
            text = "\n".join(
                [
                    f"question: {row.question_text or ''}",
                    f"finding: {row.finding_text or ''}",
                    f"response: {row.response_text or ''}",
                ]
            ).strip()
            return [("Audit Finding", text)], None

        if entity_type == "decision":
            row = db.query(Decision).filter(Decision.id == entity_id).first()
            if not row:
                return [], None
            text = "\n".join(
                [
                    f"title: {row.title or ''}",
                    f"decision_statement: {row.decision_statement or ''}",
                    f"rationale: {row.rationale_text or ''}",
                    f"risk_assessment: {row.risk_assessment_text or ''}",
                    f"final_conclusion: {row.final_conclusion or ''}",
                ]
            ).strip()
            return [("Decision", text)], None
        return [], None

    @staticmethod
    def _index_entity(db: Session, entity_type: str, entity_id: uuid.UUID, version_id: uuid.UUID | None = None):
        sections, resolved_version = SemanticPipelineService._normalize_entity(db, entity_type, entity_id, version_id)
        if not sections:
            return

        delete_query = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.entity_type == entity_type,
            KnowledgeChunk.entity_id == entity_id,
        )
        if resolved_version:
            delete_query = delete_query.filter(KnowledgeChunk.entity_version_id == resolved_version)
        delete_query.delete(synchronize_session=False)
        db.commit()

        embedder = _get_embedder()
        example_vec = embedder.encode(["dimension_probe"], normalize_embeddings=True)[0]
        SemanticPipelineService._ensure_collection(len(example_vec))
        client = _get_qdrant()

        points = []
        chunk_order = 0
        for section_name, section_text in sections:
            for text in _split_long_text(section_text):
                emb = embedder.encode([text], normalize_embeddings=True)[0].tolist()
                chunk = KnowledgeChunk(
                    tenant_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_version_id=resolved_version,
                    chunk_type="semantic_section",
                    chunk_text=text,
                    chunk_order=chunk_order,
                    metadata_json={
                        "entity_type": entity_type,
                        "entity_id": str(entity_id),
                        "version_id": str(resolved_version) if resolved_version else None,
                        "section_name": section_name,
                        "chunk_index": chunk_order,
                        "embedding_model": BGE_M3_MODEL,
                    },
                )
                db.add(chunk)
                qid = str(uuid.uuid4())
                points.append(
                    qmodels.PointStruct(
                        id=qid,
                        vector=emb,
                        payload={
                            "entity_type": entity_type,
                            "entity_id": str(entity_id),
                            "version_id": str(resolved_version) if resolved_version else None,
                            "section_name": section_name,
                            "chunk_index": chunk_order,
                            "embedding_model": BGE_M3_MODEL,
                            "chunk_text": text,
                        },
                    )
                )
                chunk_order += 1
        db.commit()
        if points:
            client.upsert(collection_name=DEFAULT_COLLECTION, points=points)

    @staticmethod
    def _generate_suggestions(db: Session, entity_type: str, entity_id: uuid.UUID):
        if entity_type not in LINK_RULES:
            return
        target_type, link_type, threshold = LINK_RULES[entity_type]
        source_chunks = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.entity_type == entity_type,
            KnowledgeChunk.entity_id == entity_id,
        ).all()
        if not source_chunks:
            return

        embedder = _get_embedder()
        client = _get_qdrant()
        entity_scores: dict[str, float] = {}
        for chunk in source_chunks[:8]:
            vec = embedder.encode([chunk.chunk_text], normalize_embeddings=True)[0].tolist()
            filt = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(key="entity_type", match=qmodels.MatchValue(value=target_type)),
                ]
            )
            if hasattr(client, "search"):
                hits = client.search(
                    collection_name=DEFAULT_COLLECTION,
                    query_vector=vec,
                    query_filter=filt,
                    limit=20,
                )
            else:
                result = client.query_points(
                    collection_name=DEFAULT_COLLECTION,
                    query=vec,
                    query_filter=filt,
                    limit=20,
                    with_payload=True,
                    with_vectors=False,
                )
                hits = result.points
            for hit in hits:
                target_id = str(hit.payload.get("entity_id"))
                if not target_id:
                    continue
                score = float(hit.score)
                entity_scores[target_id] = max(score, entity_scores.get(target_id, 0.0))

        top = sorted(entity_scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
        for target_id, score in top:
            if score < threshold:
                continue
            target_uuid = uuid.UUID(target_id)
            if SemanticPipelineService._already_linked(db, link_type, entity_id, target_uuid):
                continue
            exists = db.query(AILinkSuggestion).filter(
                AILinkSuggestion.source_entity_type == entity_type,
                AILinkSuggestion.source_entity_id == entity_id,
                AILinkSuggestion.target_entity_type == target_type,
                AILinkSuggestion.target_entity_id == target_uuid,
                AILinkSuggestion.suggested_link_type == link_type,
                AILinkSuggestion.status == "pending",
            ).first()
            if exists:
                continue
            db.add(
                AILinkSuggestion(
                    source_entity_type=entity_type,
                    source_entity_id=entity_id,
                    target_entity_type=target_type,
                    target_entity_id=target_uuid,
                    suggested_link_type=link_type,
                    score=score,
                    reason=f"Semantic similarity ({BGE_M3_MODEL}) score {score:.3f} exceeded threshold {threshold:.2f}.",
                    status="pending",
                )
            )
        db.commit()

    @staticmethod
    def _already_linked(db: Session, link_type: str, source_id: uuid.UUID, target_id: uuid.UUID) -> bool:
        if link_type == "sop-deviation":
            return db.query(SopDeviationLink).filter(SopDeviationLink.sop_id == source_id, SopDeviationLink.deviation_id == target_id).first() is not None
        if link_type == "deviation-capa":
            return db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id == source_id, DeviationCapaLink.capa_id == target_id).first() is not None
        if link_type == "capa-audit":
            return db.query(CapaAuditLink).filter(CapaAuditLink.capa_id == source_id, CapaAuditLink.audit_finding_id == target_id).first() is not None
        if link_type == "audit-decision":
            return db.query(AuditDecisionLink).filter(AuditDecisionLink.audit_finding_id == source_id, AuditDecisionLink.decision_id == target_id).first() is not None
        if link_type == "decision-sop":
            return db.query(DecisionSopLink).filter(DecisionSopLink.decision_id == source_id, DecisionSopLink.sop_id == target_id).first() is not None
        return False

    @staticmethod
    def accept_suggestion(db: Session, suggestion: AILinkSuggestion, approved_by: str | None = None):
        if suggestion.status != "pending":
            return
        link_type = suggestion.suggested_link_type
        sid = suggestion.source_entity_id
        tid = suggestion.target_entity_id
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        if not SemanticPipelineService._already_linked(db, link_type, sid, tid):
            if link_type == "sop-deviation":
                db.add(SopDeviationLink(tenant_id=tenant_id, sop_id=sid, deviation_id=tid, link_reason="ai_suggestion", confidence_score=suggestion.score, rationale_text=suggestion.reason))
            elif link_type == "deviation-capa":
                db.add(DeviationCapaLink(tenant_id=tenant_id, deviation_id=sid, capa_id=tid, link_reason="ai_suggestion", confidence_score=suggestion.score, rationale_text=suggestion.reason))
            elif link_type == "capa-audit":
                db.add(CapaAuditLink(tenant_id=tenant_id, capa_id=sid, audit_finding_id=tid, link_reason="ai_suggestion", confidence_score=suggestion.score, rationale_text=suggestion.reason))
            elif link_type == "audit-decision":
                db.add(AuditDecisionLink(tenant_id=tenant_id, audit_finding_id=sid, decision_id=tid, link_reason="ai_suggestion", confidence_score=suggestion.score, rationale_text=suggestion.reason))
            elif link_type == "decision-sop":
                db.add(DecisionSopLink(tenant_id=tenant_id, decision_id=sid, sop_id=tid, link_reason="ai_suggestion", confidence_score=suggestion.score, rationale_text=suggestion.reason))
        suggestion.status = "accepted"
        suggestion.approved_by = approved_by
        suggestion.approved_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def reject_suggestion(db: Session, suggestion: AILinkSuggestion, approved_by: str | None = None):
        if suggestion.status != "pending":
            return
        suggestion.status = "rejected"
        suggestion.approved_by = approved_by
        suggestion.approved_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def get_entity_status(db: Session, entity_type: str, entity_id: uuid.UUID) -> dict[str, Any]:
        latest_job = (
            db.query(EmbeddingJob)
            .filter(EmbeddingJob.entity_type == entity_type, EmbeddingJob.entity_id == entity_id)
            .order_by(EmbeddingJob.created_at.desc())
            .first()
        )
        counts = dict(
            db.query(AILinkSuggestion.status, func.count(AILinkSuggestion.id))
            .filter(AILinkSuggestion.source_entity_type == entity_type, AILinkSuggestion.source_entity_id == entity_id)
            .group_by(AILinkSuggestion.status)
            .all()
        )
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "latest_job_status": latest_job.status if latest_job else None,
            "latest_job_error": latest_job.error_message if latest_job else None,
            "latest_job_finished_at": latest_job.finished_at if latest_job else None,
            "pending_suggestions": int(counts.get("pending", 0)),
            "accepted_suggestions": int(counts.get("accepted", 0)),
            "rejected_suggestions": int(counts.get("rejected", 0)),
        }
