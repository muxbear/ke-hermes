from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.store import KeyValueStore
from db.engine import get_db as _get_db

_store: KeyValueStore | None = None


def set_store(store: KeyValueStore) -> None:
    global _store
    _store = store


async def get_store() -> KeyValueStore:
    assert _store is not None, "Store not initialized"
    return _store


async def get_db() -> AsyncSession:
    async for session in _get_db():
        yield session


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
