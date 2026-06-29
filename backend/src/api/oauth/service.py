"""OAuth 业务逻辑——使用策略模式 + 适配器模式处理多平台差异。"""

import logging
import uuid

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.schemas import AuthResponse, AuthTokens, UserInfo
from api.oauth.providers import get_oauth_provider
from core.security import create_token_pair
from core.cache import KeyValueCache
from db.models import Account, UserOAuth

logger = logging.getLogger(__name__)


async def get_auth_url(provider: str, store: KeyValueCache) -> str:
    """生成第三方 OAuth 授权 URL。"""
    try:
        adapter = get_oauth_provider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    state = str(uuid.uuid4())
    await store.set(f"oauth:state:{state}", provider, ttl=600)

    return adapter.build_auth_url(state)


async def handle_callback(
    provider: str,
    code: str,
    state: str,
    store: KeyValueCache,
    db: AsyncSession,
) -> AuthResponse:
    """处理 OAuth 回调——验证 state、交换 token、获取并标准化用户信息。"""
    stored_provider = await store.get(f"oauth:state:{state}")
    if not stored_provider:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    await store.delete(f"oauth:state:{state}")

    if stored_provider != provider:
        raise HTTPException(status_code=400, detail="Provider mismatch")

    try:
        adapter = get_oauth_provider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    async with httpx.AsyncClient() as http:
        token_resp = await http.post(
            adapter.token_url,
            data=adapter.get_token_params(code),
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth token exchange failed: {token_resp.text}",
            )

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token in OAuth response")

        user_resp = await http.get(
            adapter.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")

        user_data = user_resp.json()

    info = adapter.normalize_user_info(user_data)

    # 查找已有 OAuth 关联或创建新用户
    result = await db.execute(
        select(UserOAuth).where(
            UserOAuth.provider == provider,
            UserOAuth.open_id == info.open_id,
        )
    )
    oauth_record = result.scalar_one_or_none()

    if oauth_record:
        user_result = await db.execute(select(Account).where(Account.id == oauth_record.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=500, detail="Linked user not found")
    else:
        user = Account(
            nickname=info.nickname or f"{provider}_user",
            avatar=info.avatar,
            email=info.email,
            workspace_id="default",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        db.add(UserOAuth(user_id=user.id, provider=provider, open_id=info.open_id))
        await db.flush()

    token_pair = create_token_pair(user.id)
    return AuthResponse(
        tokens=AuthTokens(
            accessToken=token_pair.accessToken,
            refreshToken=token_pair.refreshToken,
            expiresIn=token_pair.expiresIn,
        ),
        user=UserInfo(
            id=user.id,
            nickname=user.nickname or "",
            avatar=user.avatar or "",
            phone=user.phone or "",
            email=user.email or "",
            workspaceId=user.workspace_id or "default",
        ),
    )
