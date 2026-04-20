"""Routes for SOP editor actions."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from action.runtime import create_action_runtime
from action.service import SOPActionService
from auth.security import get_current_user
from database.config import get_db
from database.models import AISuggestion, User
from schemas.sop_actions import (
    ActionRequest,
    ActionResponseEnvelope,
    JustifyRequest,
    SuggestionStatusResponse,
    SuggestionStatusUpdate,
)
from action.utils import utc_now_iso

router = APIRouter(prefix="/sop", tags=["SOP Editor Actions"])


def get_action_service(request: Request) -> SOPActionService:
    service = getattr(request.app.state, "sop_action_service", None)
    if service is None:
        service = SOPActionService(create_action_runtime())
        request.app.state.sop_action_service = service
    return service


@router.post("/improve", response_model=ActionResponseEnvelope)
async def improve_section(
    payload: ActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = get_action_service(request)
    return await service.improve(db, payload, current_user)


@router.post("/rewrite", response_model=ActionResponseEnvelope)
async def rewrite_section(
    payload: ActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = get_action_service(request)
    return await service.rewrite(db, payload, current_user)


@router.post("/gaps", response_model=ActionResponseEnvelope)
async def gap_check_section(
    payload: ActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = get_action_service(request)
    return await service.gap_check(db, payload, current_user)


@router.post("/convert", response_model=ActionResponseEnvelope)
async def convert_section(
    payload: ActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = get_action_service(request)
    return await service.convert(db, payload, current_user)


@router.post("/justify", response_model=ActionResponseEnvelope)
async def justify_section(
    payload: JustifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = get_action_service(request)
    return await service.justify(db, payload, current_user)


@router.patch("/suggestions/{suggestion_id}/status", response_model=SuggestionStatusResponse)
async def update_suggestion_status(
    suggestion_id: int,
    body: SuggestionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AISuggestion).where(AISuggestion.id == suggestion_id))
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if suggestion.user_id and suggestion.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this suggestion")

    suggestion.status = body.status
    suggestion.action_metadata = {
        **(suggestion.action_metadata or {}),
        "status_updated_by": str(current_user.id),
        "status_updated_to": body.status,
        "status_updated_at": utc_now_iso(),
    }
    suggestion.audit_log_snapshot = [
        *(suggestion.audit_log_snapshot or []),
        {"event": "status_updated", "status": body.status, "timestamp": utc_now_iso()},
    ]
    await db.flush()
    await db.refresh(suggestion)

    return SuggestionStatusResponse(
        id=suggestion.id,
        status=suggestion.status,
        updated_at=suggestion.updated_at,
    )
