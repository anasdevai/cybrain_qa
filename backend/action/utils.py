"""Utility helpers for SOP action processing."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from langchain_core.documents import Document
from pydantic import ValidationError

from schemas.sop_actions import (
    ConvertResponse,
    GapCheckResponse,
    ImproveResponse,
    RewriteResponse,
)


ACTION_CONTEXT_EXCERPT_CHARS = 350


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return raw


def _load_first_json_object(raw: str) -> dict[str, Any]:
    """
    Parse the first complete JSON object from a model response (ignore prose after it).
    Uses JSONDecoder.raw_decode so trailing garbage does not break parsing.
    """
    s = clean_json(raw)
    start = s.find("{")
    if start < 0:
        raise json.JSONDecodeError("no JSON object in model output", s, 0)
    decoder = json.JSONDecoder()
    data, _end = decoder.raw_decode(s, start)
    if not isinstance(data, dict):
        raise TypeError("JSON root must be an object")
    return data


def _coerce_model(data: dict[str, Any], schema: type[Any]) -> Any:
    if hasattr(schema, "model_validate"):
        return schema.model_validate(data)
    return schema(**data)  # type: ignore[call-arg]


def _plaintext_single_key_fallback(raw: str, schema: type[Any]) -> Any:
    """When the model returns the answer without JSON braces (rare but valid for power users)."""
    text = clean_json(raw).strip()
    if not text or text[0] in ("{", "["):
        raise ValueError("not plaintext fallback")
    if schema is ImproveResponse:
        return ImproveResponse(improved_text=text)
    if schema is RewriteResponse:
        return RewriteResponse(rewritten_text=text)
    if schema is GapCheckResponse:
        return GapCheckResponse(analysis=text)
    raise ValueError("not single-key schema")


def parse_model_output(raw: str, schema: type[Any]) -> Any:
    if not (raw and raw.strip()):
        raise ValueError("empty model output")
    t = clean_json(raw).lstrip()
    if schema in (ImproveResponse, RewriteResponse, GapCheckResponse) and not t.startswith(("{", "[")):
        return _plaintext_single_key_fallback(raw, schema)
    data = _load_first_json_object(raw)
    return _coerce_model(data, schema)


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
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc2:
        audit_log.append(
            {
                "event": "parse_failed",
                "attempt": 2,
                "timestamp": utc_now_iso(),
                "error": str(exc2),
            }
        )

    strict_prompt = (
        prompt
        + "\n\nCRITICAL JSON RULES (long text): Return exactly one JSON object. "
        "String values must be valid JSON strings: use \\n for newlines, \\\" for quotes, \\\\ for backslashes. "
        "Do not truncate. No markdown. No text before or after the JSON object."
    )
    third_raw = call_llm(strict_prompt)
    audit_log.append({"event": "llm_retry", "attempt": 3, "timestamp": utc_now_iso()})
    try:
        parsed = parse_model_output(third_raw, schema)
        audit_log.append({"event": "parse_success", "attempt": 3, "timestamp": utc_now_iso()})
        return parsed
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc3:
        audit_log.append(
            {
                "event": "parse_failed",
                "attempt": 3,
                "timestamp": utc_now_iso(),
                "error": str(exc3),
            }
        )
        raise HTTPException(
            status_code=422,
            detail="AI output did not match required schema after retry. Please try again.",
        ) from exc3


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
