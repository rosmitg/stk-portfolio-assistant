import json
import logging
import time
import urllib.request
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

_security = HTTPBearer()
_ALGORITHM = "ES256"
_JWKS_TTL = 3600  # seconds

_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}


def _jwks_url() -> str:
    return f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"


def _get_public_keys(*, force_refresh: bool = False) -> list[dict]:
    now = time.monotonic()
    if (
        not force_refresh
        and _jwks_cache["keys"] is not None
        and now - _jwks_cache["fetched_at"] < _JWKS_TTL
    ):
        return _jwks_cache["keys"]  # type: ignore[return-value]

    url = _jwks_url()
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            keys: list[dict] = json.loads(resp.read())["keys"]
    except Exception as exc:
        logger.error("Failed to fetch JWKS from %s: %s", url, exc)
        if _jwks_cache["keys"] is not None:
            logger.warning("Using stale JWKS cache")
            return _jwks_cache["keys"]  # type: ignore[return-value]
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service temporarily unavailable",
        ) from exc

    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def _find_key(kid: str | None, *, allow_refresh: bool = True) -> dict:
    keys = _get_public_keys()
    match = next((k for k in keys if k.get("kid") == kid), None)
    if match is None and allow_refresh:
        # kid unknown — rotation may have happened; refresh once
        keys = _get_public_keys(force_refresh=True)
        match = next((k for k in keys if k.get("kid") == kid), None)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown signing key",
        )
    return match


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
) -> str:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: missing SUPABASE_URL",
        )
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        key = _find_key(header.get("kid"))
        payload = jwt.decode(
            token,
            key,
            algorithms=[_ALGORITHM],
            options={"verify_aud": False},
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )
        return user_id
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("JWT validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
        ) from exc


CurrentUser = Annotated[str, Depends(get_current_user)]
