"""装饰器模式——系统化处理横切关注点。

提供可复用的装饰器用于缓存、重试、日志、错误处理等横切关注点，
消除 40+ 个 service 函数中的重复模板代码。
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)

AsyncFunc = Callable[..., Awaitable[Any]]


def handle_errors(
    func: AsyncFunc | None = None,
    *,
    default_message: str = "Internal server error",
) -> Any:
    """统一错误处理装饰器。

    自动捕获 HTTPException 并转换为 ApiResponse 格式。
    消除 agents_api.py 中 16 个端点的重复 try/except 模板。

    使用方式:
        @handle_errors
        async def my_endpoint(...): ...

        @handle_errors(default_message="Custom error")
        async def my_endpoint(...): ...
    """

    def decorator(fn: AsyncFunc) -> AsyncFunc:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from core.response import error as error_response

            try:
                return await fn(*args, **kwargs)
            except HTTPException as e:
                return error_response(
                    e.status_code if hasattr(e, "status_code") else 500,
                    e.detail,
                )
            except Exception:
                logger.exception("Unhandled error in %s", fn.__name__)
                return error_response(500, default_message)

        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator


def cached(ttl: int = 60):
    """API 响应缓存装饰器。

    使用全局 KeyValueStore 缓存函数返回值。

    使用方式:
        @cached(ttl=300)
        async def list_providers(...): ...
    """
    def decorator(fn: AsyncFunc) -> AsyncFunc:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from api.deps import get_store

            try:
                store = await get_store()
            except Exception:
                return await fn(*args, **kwargs)

            cache_key = f"cache:{fn.__name__}:{hash(str(args))}:{hash(str(kwargs))}"
            try:
                cached_value = await store.get(cache_key)
                if cached_value is not None:
                    logger.debug("Cache hit: %s", fn.__name__)
                    return cached_value
            except Exception:
                pass

            result = await fn(*args, **kwargs)
            try:
                await store.set(cache_key, result, ttl=ttl)
            except Exception:
                pass
            return result

        return wrapper  # type: ignore[return-value]
    return decorator


def retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """指数退避重试装饰器。

    用于处理瞬时错误（网络超时、数据库连接断开等）。

    使用方式:
        @retry(max_attempts=3)
        async def call_external_api(...): ...
    """
    def decorator(fn: AsyncFunc) -> AsyncFunc:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except HTTPException:
                    raise
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        wait = backoff_factor ** attempt
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s",
                            attempt + 1,
                            max_attempts,
                            fn.__name__,
                            wait,
                            e,
                        )
                        await asyncio.sleep(wait)
            raise last_exc  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]
    return decorator


def rate_limit(max_calls: int = 5, period_seconds: int = 60, key_prefix: str = "rate_limit"):
    """请求频率限制装饰器——基于 KeyValueStore 的滑动窗口计数器。

    使用方式:
        @rate_limit(max_calls=5, period_seconds=60, key_prefix="sms")
        async def send_sms(...): ...

    按 IP + 函数名生成唯一 key，超过限制返回 429。
    """

    def decorator(fn: AsyncFunc) -> AsyncFunc:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from fastapi import HTTPException, Request

            from api.deps import get_store

            # 提取请求对象（约定第一个位置参数或 kwargs 中名为 request 的参数）
            request: Request | None = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if request is not None:
                try:
                    store = await get_store()
                except Exception:
                    return await fn(*args, **kwargs)

                client_ip = request.client.host if request.client else "unknown"
                rate_key = f"{key_prefix}:{fn.__name__}:{client_ip}"
                current = await store.get(rate_key)
                count = int(current) if current else 0

                if count >= max_calls:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Try again in {period_seconds}s.",
                    )

                if count == 0:
                    await store.set(rate_key, "1", ttl=period_seconds)
                else:
                    await store.incr(rate_key)

            return await fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]
    return decorator


def log_call(level: int = logging.DEBUG):
    """自动函数调用日志装饰器。

    使用方式:
        @log_call()
        async def my_service(...): ...
    """
    def decorator(fn: AsyncFunc) -> AsyncFunc:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.log(level, "CALL %s", fn.__name__)
            try:
                result = await fn(*args, **kwargs)
                logger.log(level, "RETURN %s -> %s", fn.__name__, type(result).__name__)
                return result
            except Exception as e:
                logger.log(level, "ERROR %s -> %s", fn.__name__, type(e).__name__)
                raise

        return wrapper  # type: ignore[return-value]
    return decorator
