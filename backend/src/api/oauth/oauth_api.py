from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.schemas import AuthResponse
from api.deps import get_db, get_store
from api.oauth.schemas import OAuthCallbackRequest
from api.oauth.service import get_auth_url, handle_callback
from core.response import ApiResponse, error, ok
from core.store import KeyValueStore

router = APIRouter(prefix="/api/oauth", tags=["oauth"])


@router.get("/auth-url")
async def auth_url(
    provider: str,
    store: KeyValueStore = Depends(get_store),
):
    try:
        url = await get_auth_url(provider, store)
        return ok({"authUrl": url})
    except HTTPException as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
    except Exception as e:
        raise


@router.post("/callback", response_model=ApiResponse[AuthResponse])
async def callback(
    req: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    store: KeyValueStore = Depends(get_store),
):
    try:
        result = await handle_callback(req.provider, req.code, req.state, store, db)
        return ok(result)
    except HTTPException as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
    except Exception as e:
        raise
