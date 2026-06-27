import logging
from datetime import date as date_type
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.models.brief import Brief
from app.services.database import get_db

router = APIRouter(prefix="/brief", tags=["brief"])
logger = logging.getLogger(__name__)

Db = Annotated[Optional[AsyncSession], Depends(get_db)]


class BriefResponse(BaseModel):
    """Full brief payload returned by GET /today and POST /generate."""

    user_id: str
    date: date_type
    headline: str
    portfolio_health: int
    sections: list = []
    alerts: list = []

    model_config = {"from_attributes": True}


class BriefSummary(BaseModel):
    """Condensed brief row for the history list."""

    date: date_type
    headline: str
    portfolio_health: int

    model_config = {"from_attributes": True}


@router.get("/today", response_model=BriefResponse)
async def get_today_brief(user_id: CurrentUser, db: Db) -> Brief:
    """Return today's brief for the authenticated user, or 404 if none yet."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured",
        )

    result = await db.execute(
        select(Brief).where(
            Brief.user_id == user_id,
            Brief.date == date_type.today(),
        )
    )
    brief = result.scalar_one_or_none()
    if brief is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No brief generated yet today",
        )
    return brief


@router.get("/history", response_model=list[BriefSummary])
async def get_brief_history(user_id: CurrentUser, db: Db) -> list[Brief]:
    """Return the user's past briefs (most recent first), summary fields only."""
    if db is None:
        return []

    result = await db.execute(
        select(Brief)
        .where(Brief.user_id == user_id)
        .order_by(Brief.date.desc())
    )
    return list(result.scalars().all())


@router.post("/generate")
async def generate_brief(user_id: CurrentUser) -> JSONResponse:
    """Trigger brief generation for the current user via the Watchman service.

    STK authenticates the user here (CurrentUser) against its own Supabase, then
    calls Watchman as a trusted service: it sends the shared internal secret and
    the validated user_id, rather than forwarding the user's JWT (STK and
    Watchman use separate Supabase projects, so the JWT wouldn't validate there).
    Watchman's response is relayed back to the STK frontend unchanged.
    """
    url = f"{settings.watchman_backend_url}/api/v1/brief/generate"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                url,
                headers={"X-Internal-Secret": settings.internal_service_secret},
                json={"user_id": user_id},
            )
    except httpx.RequestError as exc:
        logger.warning("Watchman service unreachable at %s: %s", url, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Brief generation service unavailable",
        ) from exc

    # Relay Watchman's response (success or error) to the frontend unchanged.
    try:
        content = resp.json()
    except ValueError:
        content = {"detail": resp.text}
    return JSONResponse(status_code=resp.status_code, content=content)
