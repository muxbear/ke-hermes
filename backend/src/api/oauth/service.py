import logging
import uuid

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.config import settings
from api.auth.schemas import AuthResponse, AuthTokens, UserInfo
from core.security import create_token_pair
from core.store import KeyValueStore
from db.models import User, UserOAuth

logger = logging.getLogger(__name__)

PROVIDER_CONFIGS = {
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user",
        "client_id": lambda: settings.OAUTH_GITHUB_CLIENT_ID,
        "client_secret": lambda: settings.OAUTH_GITHUB_CLIENT_SECRET,
    },
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid profile email",
        "client_id": lambda: settings.OAUTH_GOOGLE_CLIENT_ID,
        "client_secret": lambda: settings.OAUTH_GOOGLE_CLIENT_SECRET,
    },
    "wechat": {
        "auth_url": "https://open.weixin.qq.com/connect/qrconnect",
        "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
        "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
        "scope": "snsapi_login",
        "client_id": lambda: settings.OAUTH_WECHAT_CLIENT_ID,
        "client_secret": lambda: settings.OAUTH_WECHAT_CLIENT_SECRET,
    },
}

REDIRECT_URI = "http://localhost:5173/oauth/callback"


async def get_auth_url(provider: str, store: KeyValueStore) -> str:
    cfg = PROVIDER_CONFIGS.get(provider)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    client_id = cfg["client_id"]()
    if not client_id:
        raise HTTPException(
            status_code=501,
            detail=f"{provider} OAuth not configured (missing client_id)",
        )

    state = str(uuid.uuid4())
    await store.set(f"oauth:state:{state}", provider, ttl=600)

    auth_url = (
        f"{cfg['auth_url']}?"
        f"client_id={client_id}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={cfg['scope']}&"
        f"state={state}"
        + ("&response_type=code" if provider == "wechat" else "&response_type=code")
    )
    return auth_url


async def handle_callback(
    provider: str,
    code: str,
    state: str,
    store: KeyValueStore,
    db: AsyncSession,
) -> AuthResponse:
    stored_provider = await store.get(f"oauth:state:{state}")
    if not stored_provider:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    await store.delete(f"oauth:state:{state}")

    if stored_provider != provider:
        raise HTTPException(status_code=400, detail="Provider mismatch")

    cfg = PROVIDER_CONFIGS.get(provider)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    client_id = cfg["client_id"]()
    client_secret = cfg["client_secret"]()

    async with httpx.AsyncClient() as http:
        token_resp = await http.post(
            cfg["token_url"],
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"OAuth token exchange failed: {token_resp.text}")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token in OAuth response")

        user_resp = await http.get(
            cfg["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")

        user_data = user_resp.json()

    open_id = str(user_data.get("id", ""))
    nickname = user_data.get("login") or user_data.get("name") or user_data.get("nickname", "")
    avatar = user_data.get("avatar_url") or user_data.get("picture", "")
    email = user_data.get("email", "")

    result = await db.execute(
        select(UserOAuth).where(
            UserOAuth.provider == provider,
            UserOAuth.open_id == open_id,
        )
    )
    oauth_record = result.scalar_one_or_none()

    if oauth_record:
        user_result = await db.execute(select(User).where(User.id == oauth_record.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=500, detail="Linked user not found")
    else:
        user = User(
            nickname=nickname or f"{provider}_user",
            avatar=avatar,
            email=email,
            workspace_id="default",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        db.add(UserOAuth(user_id=user.id, provider=provider, open_id=open_id))
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
