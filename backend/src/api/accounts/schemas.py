"""Account management API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CamelCaseModel(BaseModel):
    """Base model that serializes using aliases (camelCase output)."""

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


# ── Request schemas ────────────────────────────────────────────

class AccountCreateRequest(BaseModel):
    """Create a login account."""

    username: str = Field(min_length=2, max_length=64)
    nickname: str = Field(default="", max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: str = Field(default="", max_length=128)
    phone: str = Field(default="", max_length=20)
    is_active: bool = True


class AccountUpdateRequest(BaseModel):
    """Update account info. Non-None fields are applied."""

    username: str | None = Field(default=None, min_length=2, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class AccountPasswordChangeRequest(BaseModel):
    """Change own password."""

    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class AccountListParams(BaseModel):
    """Query parameters for account list."""

    search: str = ""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ── Response schemas ───────────────────────────────────────────

class AccountResponse(CamelCaseModel):
    """Account info for list/detail."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    username: str = ""
    nickname: str = ""
    email: str = ""
    phone: str = ""
    avatar: str = ""
    is_active: bool = Field(serialization_alias="isActive")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class AccountListResponse(CamelCaseModel):
    """Paginated account list."""

    items: list[AccountResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class AccountResetPasswordResponse(CamelCaseModel):
    """Response after admin resets a password."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    temp_password: str = Field(serialization_alias="tempPassword")
