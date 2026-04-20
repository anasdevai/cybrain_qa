"""
Runtime endpoint-to-Qdrant auto sync.

Polls upstream API endpoints, detects added/updated/deleted documents, and
reuses the webhook sync pipeline to keep Qdrant collections current.
"""

import asyncio
import hashlib
import json
import logging
import os
from typing import Any, Callable, Dict

import httpx
from langchain_core.documents import Document

from ingestion.multi_fetcher import (
    HEADERS,
    BASE_URL,
    _clean_audit,
    _clean_capa,
    _clean_decision,
    _clean_deviation,
    _clean_sop,
)
from routers.webhooks import _process_sync


Cleaner = Callable[[dict], Document | None]

ENTITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "sops": {"path": "/api/sops", "cleaner": _clean_sop},
    "deviations": {"path": "/api/deviations", "cleaner": _clean_deviation},
    "capas": {"path": "/api/capas", "cleaner": _clean_capa},
    "decisions": {"path": "/api/decisions", "cleaner": _clean_decision},
    "audits": {"path": "/api/audits", "cleaner": _clean_audit},
}


def _is_enabled() -> bool:
    raw = os.getenv("ENABLE_ENDPOINT_AUTO_SYNC", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _interval_seconds() -> int:
    try:
        value = int(os.getenv("ENDPOINT_SYNC_INTERVAL_SECONDS", "60"))
        return max(15, value)
    except ValueError:
        return 60


def _api_base_url() -> str:
    return os.getenv("API_BASE_URL", BASE_URL).rstrip("/")


def _extract_source_id(doc: Document, raw_item: dict) -> str:
    source_id = str(doc.metadata.get("source_id", "")).strip()
    if source_id:
        return source_id
    fallback = raw_item.get("id")
    return str(fallback).strip() if fallback is not None else ""


def _fingerprint(doc: Document) -> str:
    stable_payload = {
        "page_content": doc.page_content,
        "metadata": doc.metadata,
    }
    blob = json.dumps(stable_payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


async def _fetch_list(client: httpx.AsyncClient, path: str) -> list:
    base_url = _api_base_url()
    if not base_url:
        raise ValueError("API_BASE_URL is not set; runtime sync cannot fetch endpoint data.")
    resp = await client.get(f"{base_url}{path}", headers=HEADERS)
    print(f"[AUTO_SYNC] Fetching {path} (Base: {base_url}) - Status: {resp.status_code}")
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        print(f"[AUTO_SYNC]   Found {len(data)} items in list")
        return data
    if isinstance(data, dict):
        return data.get("results", data.get("data", []))
    return []


class RuntimeEndpointSync:
    def __init__(self) -> None:
        self.enabled = _is_enabled()
        self.interval = _interval_seconds()
        self._state: Dict[str, Dict[str, str]] = {entity: {} for entity in ENTITY_CONFIG}

    async def run_forever(self) -> None:
        if not self.enabled:
            logging.info("[AUTO_SYNC] Disabled by ENABLE_ENDPOINT_AUTO_SYNC")
            return

        logging.info("[AUTO_SYNC] Started. Interval=%ss", self.interval)

        while True:
            try:
                await self._sync_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logging.exception("[AUTO_SYNC] Sync cycle failed: %s", exc)

            await asyncio.sleep(self.interval)

    async def _sync_once(self) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            for entity, cfg in ENTITY_CONFIG.items():
                await self._sync_entity(client, entity, cfg["path"], cfg["cleaner"])

    async def _sync_entity(
        self,
        client: httpx.AsyncClient,
        entity: str,
        path: str,
        cleaner: Cleaner,
    ) -> None:
        raw_items = await _fetch_list(client, path)
        current: Dict[str, str] = {}
        changed_count = 0

        for item in raw_items:
            doc = cleaner(item)
            if doc is None:
                print(f"[AUTO_SYNC]   [SKIP] Cleaner returned None for item {item.get('id', 'unknown')}")
                continue

            source_id = _extract_source_id(doc, item)
            if not source_id:
                print(f"[AUTO_SYNC]   [SKIP] No source_id found for item {item.get('id', 'unknown')}")
                continue

            fp = _fingerprint(doc)
            current[source_id] = fp

            previous_fp = self._state[entity].get(source_id)
            if previous_fp != fp:
                ok = await asyncio.to_thread(_process_sync, entity, "update", item)
                if ok:
                    changed_count += 1
                else:
                    # Keep old fingerprint so failed sync retries on next cycle.
                    if previous_fp is not None:
                        current[source_id] = previous_fp

        removed_ids = set(self._state[entity].keys()) - set(current.keys())
        for source_id in removed_ids:
            ok = await asyncio.to_thread(
                _process_sync,
                entity,
                "delete",
                {"id": source_id, "entity_type": entity, "action": "delete"},
            )
            if ok:
                changed_count += 1
            else:
                current[source_id] = self._state[entity].get(source_id, "")

        self._state[entity] = current
        if changed_count:
            logging.info(
                "[AUTO_SYNC] %s: applied %s change(s) from endpoint %s",
                entity,
                changed_count,
                path,
            )

