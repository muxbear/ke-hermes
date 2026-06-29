"""Request and response schemas for personnel management."""

from datetime import date  # noqa: F401
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CamelCaseModel(BaseModel):
    """Base model that serializes using aliases (camelCase output)."""

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


# ── Request schemas ────────────────────────────────────────────

class PersonnelCreateRequest(BaseModel):
    """Create a personnel record, optionally with a login account."""

    name: str = Field(min_length=1, max_length=64)
    employee_id: str = Field(min_length=1, max_length=64)
    dept_id: str = ""
    position: str = ""
    email: str = ""
    phone: str = ""
    status: str = Field(default="active", pattern=r"^(active|inactive|pending)$")
    join_date: str = ""
    avatar: str = ""
    user_id: str | None = None
    create_account: bool = False


class PersonnelUpdateRequest(BaseModel):
    """Update a personnel record. Only non-None fields are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    employee_id: str | None = Field(default=None, min_length=1, max_length=64)
    dept_id: str | None = None
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = Field(default=None, pattern=r"^(active|inactive|pending)$")
    join_date: str | None = None
    avatar: str | None = None
    user_id: str | None = None


# ── Response schemas ───────────────────────────────────────────

class PersonnelResponse(CamelCaseModel):
    """SystemUser projection for the personnel management page."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    employee_id: str = Field(serialization_alias="employeeId")
    dept_id: str = Field(default="", serialization_alias="deptId")
    position: str = ""
    email: str = ""
    phone: str = ""
    status: str
    join_date: str = Field(default="", serialization_alias="joinDate")
    avatar: str = ""
    user_id: str | None = Field(default=None, serialization_alias="userId")
    account_created: bool = Field(default=False, serialization_alias="accountCreated")
    username: str = ""
    temp_password: str = Field(default="", serialization_alias="tempPassword")
