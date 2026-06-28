from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import KeyValueCache
from core.security import decode_token
from db.engine import get_db as _get_db

_cache: KeyValueCache | None = None


def set_cache(cache: KeyValueCache) -> None:
    global _cache
    _cache = cache


async def get_cache() -> KeyValueCache:
    assert _cache is not None, "Cache 未被初始化"
    return _cache


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

async def get_current_user_id(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth.split(" ", 1)[1] # auth.split(" ", 1), 对 auth 使用 " " 进行分割, 1 表示分割 1 次
    # 1.验证签名 2.检查过期时间 3.检查类型: "access" 可能用于验证 Token 的用途（例如区分 access token 和 refresh token）。
    # payload: 如果验证通过，返回 Token 中携带的数据载荷（通常是一个字典），包含用户ID、过期时间等信息。如果验证失败，该函数内部通常会直接抛出异常（如 401 或 403）
    payload = decode_token(token, "access")
    return str(payload["sub"])