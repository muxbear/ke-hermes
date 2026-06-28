from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.schemas import AuthResponse
from api.deps import get_db, get_cache
from api.oauth.schemas import OAuthCallbackRequest
from api.oauth.service import get_auth_url, handle_callback
from core.decorators import handle_errors
from core.response import ApiResponse, ok
from core.cache import KeyValueCache

router = APIRouter(prefix="/api/oauth", tags=["oauth"])


@router.get("/auth-url")
@handle_errors
async def auth_url(
    provider: str,
    cache: KeyValueCache = Depends(get_cache),
):
    url = await get_auth_url(provider, cache)
    return ok({"authUrl": url})


@router.post("/callback", response_model=ApiResponse[AuthResponse])
@handle_errors
async def callback(
    req: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    cache: KeyValueCache = Depends(get_cache),
):
    result = await handle_callback(req.provider, req.code, req.state, cache, db)
    return ok(result)
