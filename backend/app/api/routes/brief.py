import logging
from datetime import date as date_type
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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

# Bearer scheme used to capture the raw token so it can be forwarded to Watchman.
_bearer = HTTPBearer()
BearerToken = Annotated[HTTPAuthorizationCredentials, Depends(_bearer)]


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
async def generate_brief(user_id: CurrentUser, credentials: BearerToken) -> JSONResponse:
    """Trigger brief generation for the current user via the Watchman service.

    Watchman runs the LangGraph pipeline in its own backend. We forward the
    caller's bearer token so Watchman authenticates the same user, then relay
    Watchman's response (status and body) straight back to the STK frontend.
    """
    url = f"{settings.watchman_backend_url}/api/v1/brief/generate"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {credentials.credentials}"},
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
