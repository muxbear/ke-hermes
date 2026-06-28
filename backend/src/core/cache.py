import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod

from agent.config import settings

logger = logging.getLogger(__name__)


class KeyValueCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def incr(self, key: str) -> int: ...

    @abstractmethod
    async def ttl(self, key: str) -> int: ...


class MemoryCache(KeyValueCache):
    """Thread-safe in-memory cache with lazy TTL eviction."""

    def __init__(self):
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.monotonic()

    def _clean(self, key: str):
        entry = self._data.get(key)
        if entry and self._now() > entry[1]:
            del self._data[key]

    async def get(self, key: str) -> str | None:
        with self._lock:
            self._clean(key)
            entry = self._data.get(key)
            return entry[0] if entry else None

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        with self._lock:
            self._data[key] = (value, self._now() + ttl)

    async def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    async def exists(self, key: str) -> bool:
        v = await self.get(key)
        return v is not None

    async def incr(self, key: str) -> int:
        with self._lock:
            self._clean(key)
            entry = self._data.get(key)
            if entry:
                val = int(entry[0].split(":")[0]) + 1
            else:
                val = 1
            self._data[key] = (str(val), entry[1] if entry else self._now() + 86400)
            return val

    async def ttl(self, key: str) -> int:
        with self._lock:
            entry = self._data.get(key)
            if not entry:
                return -2  # key does not exist
            remaining = entry[1] - self._now()
            return max(0, int(remaining))


async def create_cache(redis_url: str = "") -> KeyValueCache:
    """如果 Redis 可用，创建 RedisCache，否则回退到 MemoryCache。"""
    if not redis_url:
        redis_url = settings.REDIS_URL
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(redis_url)
        r.ping()
        logger.info(f"从 {redis_url} 连接到 Redis")

        class RedisCache(KeyValueCache):
            def __init__(self, client):
                self._r = client

            async def get(self, key: str) -> str | None:
                v = await self._r.get(key)
                return v.decode() if v else None

            async def set(self, key: str, value: str, ttl: int = 300) -> None:
                await self._r.setex(key, ttl, value)

            async def delete(self, key: str) -> None:
                await self._r.delete(key)

            async def exists(self, key: str) -> bool:
                return await self._r.exists(key) > 0

            async def incr(self, key: str) -> int:
                return await self._r.incr(key)

            async def ttl(self, key: str) -> int:
                return await self._r.ttl(key)

        return RedisCache(r)
    except Exception as e:
        logger.warning("Redis 不可用 (%s), 使用 in-memory store", e)
        return MemoryCache()
