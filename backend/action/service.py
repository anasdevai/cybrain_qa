"""Backend service layer for SOP editor actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.sop_actions import (
    ActionRequest,
    ActionResponseEnvelope,
    ConvertResponse,
    GapCheckResponse,
    ImproveResponse,
    JustifyRequest,
    JustifyResponse,
    RewriteResponse,
    VALID_CHANGE_CATEGORIES,
)
from database.models import AISuggestion, User

from action.prompts import (
    build_convert_prompt,
    build_convert_retry_prompt,
    build_gap_check_prompt,
    build_improve_prompt,
    build_justify_prompt,
    build_rewrite_prompt,
)
from action.runtime import ActionRuntime
from action.utils import (
    extract_source_titles,
    format_chunks,
    parse_with_retry,
    utc_now_iso,
    validate_convert_response,
)


@dataclass
class ActionExecution:
    result: dict[str, Any]
    related_documents: list[str]
    metadata_snapshot: dict[str, Any]
    audit_log_snapshot: list[dict[str, Any]]


class SOPActionService:
    def __init__(self, runtime: ActionRuntime):
        self.runtime = runtime

    def _build_gap_check_retrieval_query(self, request: ActionRequest) -> str:
        parts = [
            f"SOP: {request.sop_title}",
            f"Section: {request.section_title}",
            f"Type: {request.section_type}",
            request.section_text,
        ]
        return "\n".join(part.strip() for part in parts if part and part.strip())

    def _call_llm(self, prompt: str) -> str:
        parser = StrOutputParser()
        try:
            return (self.runtime.llm | parser).invoke(prompt)
        except Exception:
            return (self.runtime.fallback_llm | parser).invoke(prompt)

    def _retrieve_context(
        self,
        section_text: str,
        audit_log: list[dict[str, Any]],
        *,
        retrieval_query: str | None = None,
    ) -> tuple[list[Document], list[float]]:
        query_text = (retrieval_query or section_text).strip()
        raw_docs = self.runtime.retriever.invoke(query_text)
        audit_log.append(
            {
                "event": "hybrid_retrieval_completed",
                "timestamp": utc_now_iso(),
                "documents_retrieved": len(raw_docs),
                "collection": self.runtime.collection_name,
                "retrieval_query_preview": query_text[:220],
            }
        )
        reranked = self.runtime.reranker.rerank_top_n(query_text, raw_docs, 3)
        audit_log.append(
            {
                "event": "rerank_completed",
                "timestamp": utc_now_iso(),
                "documents_reranked": len(reranked),
            }
        )
        return reranked, []

    async def _save_suggestion(
        self,
        *,
        db: AsyncSession,
        request: ActionRequest,
        action_type: str,
        result: dict[str, Any],
        related_documents: list[str],
        metadata_snapshot: dict[str, Any],
        audit_log_snapshot: list[dict[str, Any]],
        current_user: User | None,
    ) -> AISuggestion:
        suggestion = AISuggestion(
            document_id=request.document_id,
            section_id=request.section_id,
            section_title=request.section_title,
            section_type=request.section_type,
            action_type=action_type,
            input_text=request.section_text,
            output_text=result,
            related_documents=related_documents,
            metadata_snapshot=metadata_snapshot,
            audit_log_snapshot=audit_log_snapshot,
            action_metadata={
                "sop_title": request.sop_title,
                "service": "sop_editor_actions",
                "related_document_count": len(related_documents),
            },
            status="pending",
            user_id=getattr(current_user, "id", None),
        )
        db.add(suggestion)
        await db.flush()
        await db.refresh(suggestion)
        return suggestion

    async def _run_rag_action(
        self,
        *,
        db: AsyncSession,
        request: ActionRequest,
        action_type: str,
        schema: type[Any],
        prompt_builder,
        current_user: User | None,
    ) -> ActionResponseEnvelope:
        audit_log: list[dict[str, Any]] = [{"event": "action_started", "timestamp": utc_now_iso(), "action": action_type}]
        retrieval_query = self._build_gap_check_retrieval_query(request) if action_type == "gap_check" else request.section_text
        chunks, query_vector = self._retrieve_context(
            request.section_text,
            audit_log,
            retrieval_query=retrieval_query,
        )
        related_documents = extract_source_titles(chunks)
        context = format_chunks(chunks)
        prompt = prompt_builder(request, context)
        raw = self._call_llm(prompt)
        audit_log.append({"event": "llm_completed", "timestamp": utc_now_iso(), "action": action_type})
        parsed = parse_with_retry(
            raw=raw,
            schema=schema,
            prompt=prompt,
            call_llm=self._call_llm,
            audit_log=audit_log,
        )
        metadata_snapshot = {
            "query_vector_size": 0,
            "collection_name": self.runtime.collection_name,
            "rag_mode": "hybrid",
            "retrieval_query": retrieval_query[:500],
            "fusion_weights": {"dense": self.runtime.retriever.dense_weight, "bm25": self.runtime.retriever.bm25_weight},
            "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "llm_model": getattr(self.runtime.llm, "model", None),
        }
        suggestion = await self._save_suggestion(
            db=db,
            request=request,
            action_type=action_type,
            result=parsed.model_dump(),
            related_documents=related_documents,
            metadata_snapshot=metadata_snapshot,
            audit_log_snapshot=audit_log,
            current_user=current_user,
        )
        return ActionResponseEnvelope(
            suggestion_id=suggestion.id,
            result=parsed.model_dump(),
            related_documents=related_documents,
            action_type=action_type,
            status=suggestion.status,
        )

    async def improve(self, db: AsyncSession, request: ActionRequest, current_user: User | None) -> ActionResponseEnvelope:
        return await self._run_rag_action(
            db=db,
            request=request,
            action_type="improve",
            schema=ImproveResponse,
            prompt_builder=build_improve_prompt,
            current_user=current_user,
        )

    async def rewrite(self, db: AsyncSession, request: ActionRequest, current_user: User | None) -> ActionResponseEnvelope:
        return await self._run_rag_action(
            db=db,
            request=request,
            action_type="rewrite",
            schema=RewriteResponse,
            prompt_builder=build_rewrite_prompt,
            current_user=current_user,
        )

    async def gap_check(self, db: AsyncSession, request: ActionRequest, current_user: User | None) -> ActionResponseEnvelope:
        return await self._run_rag_action(
            db=db,
            request=request,
            action_type="gap_check",
            schema=GapCheckResponse,
            prompt_builder=build_gap_check_prompt,
            current_user=current_user,
        )

    async def convert(self, db: AsyncSession, request: ActionRequest, current_user: User | None) -> ActionResponseEnvelope:
        audit_log: list[dict[str, Any]] = [{"event": "action_started", "timestamp": utc_now_iso(), "action": "convert"}]
        prompt = build_convert_prompt(request)
        raw = self._call_llm(prompt)
        audit_log.append({"event": "llm_completed", "timestamp": utc_now_iso(), "action": "convert"})
        try:
            parsed = parse_with_retry(
                raw=raw,
                schema=ConvertResponse,
                prompt=build_convert_retry_prompt(request),
                call_llm=self._call_llm,
                audit_log=audit_log,
            )
            validate_convert_response(parsed)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Convert output is incomplete. Please try again.") from exc

        metadata_snapshot = {
            "collection_name": None,
            "fusion_weights": None,
            "reranker": None,
            "llm_model": getattr(self.runtime.llm, "model", None),
        }
        suggestion = await self._save_suggestion(
            db=db,
            request=request,
            action_type="convert",
            result=parsed.model_dump(),
            related_documents=[],
            metadata_snapshot=metadata_snapshot,
            audit_log_snapshot=audit_log,
            current_user=current_user,
        )
        return ActionResponseEnvelope(
            suggestion_id=suggestion.id,
            result=parsed.model_dump(),
            related_documents=[],
            action_type="convert",
            status=suggestion.status,
        )

    async def justify(self, db: AsyncSession, request: JustifyRequest, current_user: User | None) -> ActionResponseEnvelope:
        audit_log: list[dict[str, Any]] = [{"event": "action_started", "timestamp": utc_now_iso(), "action": "justify"}]
        prompt = build_justify_prompt(request)
        raw = self._call_llm(prompt)
        audit_log.append({"event": "llm_completed", "timestamp": utc_now_iso(), "action": "justify"})
        parsed = parse_with_retry(
            raw=raw,
            schema=JustifyResponse,
            prompt=prompt,
            call_llm=self._call_llm,
            audit_log=audit_log,
        )

        result = parsed.model_dump()
        if result["change_category"] not in VALID_CHANGE_CATEGORIES:
            result["change_category"] = "clarity_improvement"

        metadata_snapshot = {
            "collection_name": None,
            "fusion_weights": None,
            "reranker": None,
            "llm_model": getattr(self.runtime.llm, "model", None),
            "change_type": request.change_type,
        }
        suggestion = await self._save_suggestion(
            db=db,
            request=request,
            action_type="justify",
            result=result,
            related_documents=[],
            metadata_snapshot=metadata_snapshot,
            audit_log_snapshot=audit_log,
            current_user=current_user,
        )
        return ActionResponseEnvelope(
            suggestion_id=suggestion.id,
            result=result,
            related_documents=[],
            action_type="justify",
            status=suggestion.status,
        )
