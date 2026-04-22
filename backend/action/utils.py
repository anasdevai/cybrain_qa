"""Utility helpers for SOP action processing."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from langchain_core.documents import Document
from pydantic import ValidationError

from schemas.sop_actions import ConvertResponse


ACTION_CONTEXT_EXCERPT_CHARS = 350


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return raw


def parse_model_output(raw: str, schema: type[Any]) -> Any:
    data = json.loads(clean_json(raw))
    return schema(**data)


def parse_with_retry(
    *,
    raw: str,
    schema: type[Any],
    prompt: str,
    call_llm,
    audit_log: list[dict[str, Any]],
) -> Any:
    try:
        parsed = parse_model_output(raw, schema)
        audit_log.append({"event": "parse_success", "attempt": 1, "timestamp": utc_now_iso()})
        return parsed
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        audit_log.append(
            {
                "event": "parse_failed",
                "attempt": 1,
                "timestamp": utc_now_iso(),
                "error": str(exc),
            }
        )

    retry_prompt = (
        prompt
        + "\n\nCRITICAL INSTRUCTION: Your previous response was not valid JSON. "
        + "Return ONLY the JSON object. No markdown. No explanation."
    )
    retry_raw = call_llm(retry_prompt)
    audit_log.append({"event": "llm_retry", "attempt": 2, "timestamp": utc_now_iso()})

    try:
        parsed = parse_model_output(retry_raw, schema)
        audit_log.append({"event": "parse_success", "attempt": 2, "timestamp": utc_now_iso()})
        return parsed
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        audit_log.append(
            {
                "event": "parse_failed",
                "attempt": 2,
                "timestamp": utc_now_iso(),
                "error": str(exc),
            }
        )
        raise HTTPException(
            status_code=422,
            detail="AI output did not match required schema after retry. Please try again.",
        ) from exc


def validate_convert_response(parsed: ConvertResponse) -> None:
    missing: list[str] = []
    if len(parsed.purpose.strip()) < 10:
        missing.append("purpose")
    if len(parsed.scope.strip()) < 10:
        missing.append("scope")
    if len(parsed.responsibilities.strip()) < 10:
        missing.append("responsibilities")
    if not parsed.procedure or not any(step.strip() for step in parsed.procedure):
        missing.append("procedure")
    if len(parsed.documentation.strip()) < 10:
        missing.append("documentation")

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Convert output is incomplete. Missing or empty sections: {', '.join(missing)}",
        )


def format_chunks(chunks: list[Document]) -> str:
    if not chunks:
        return "No relevant context found."

    formatted: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.metadata or {}
        source = (
            metadata.get("title")
            or metadata.get("sop_title")
            or metadata.get("source")
            or metadata.get("document_title")
            or metadata.get("sop_number")
            or f"Source {index}"
        )
        excerpt = chunk.page_content[:ACTION_CONTEXT_EXCERPT_CHARS].strip()
        formatted.append(f"[{source}]\n{excerpt}")
    return "\n\n".join(formatted)


def extract_source_titles(chunks: list[Document]) -> list[str]:
    seen: set[str] = set()
    titles: list[str] = []
    for chunk in chunks:
        metadata = chunk.metadata or {}
        title = (
            metadata.get("title")
            or metadata.get("sop_title")
            or metadata.get("source")
            or metadata.get("document_title")
            or metadata.get("sop_number")
        )
        if title and title not in seen:
            seen.add(title)
            titles.append(str(title))
    return titles
