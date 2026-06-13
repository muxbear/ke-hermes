import time
import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "ok"
    requestId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = Field(default_factory=lambda: int(time.time()))


def ok(data: T = None, message: str = "ok") -> ApiResponse[T]:
    return ApiResponse(code=0, data=data, message=message)


def error(code: int, message: str) -> ApiResponse[Any]:
    return ApiResponse(code=code, data=None, message=message)
