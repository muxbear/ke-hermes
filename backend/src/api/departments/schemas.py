"""Request and response schemas for department / org node management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CamelCaseModel(BaseModel):
    """Base model that serializes using aliases (camelCase output)."""

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


# ── Enums ──────────────────────────────────────────────────────
ORG_TYPE_VALUES = ("group", "center", "dept", "team")
ORG_STATUS_VALUES = ("active", "inactive")


# ── Request schemas ────────────────────────────────────────────

class DepartmentCreateRequest(BaseModel):
    """Create a department (org node)."""

    name: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=64)
    parent_id: str | None = None
    type: str = Field(default="dept", pattern=r"^(group|center|dept|team)$")
    level: int = Field(default=0, ge=0)
    manager_id: str | None = None
    description: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    sort: int = 0
    status: str = Field(default="active", pattern=r"^(active|inactive)$")


class DepartmentUpdateRequest(BaseModel):
    """Update a department. Only non-None fields are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    code: str | None = Field(default=None, min_length=1, max_length=64)
    parent_id: str | None = None
    type: str | None = Field(default=None, pattern=r"^(group|center|dept|team)$")
    level: int | None = Field(default=None, ge=0)
    manager_id: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    sort: int | None = None
    status: str | None = Field(default=None, pattern=r"^(active|inactive)$")


class DepartmentDeleteRequest(BaseModel):
    """Batch delete departments by IDs."""

    ids: list[str] = Field(min_length=1)


# ── Response schemas (OrgNode projection) ──────────────────────

class OrgNodeResponse(CamelCaseModel):
    """Full org node for the org management page."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    code: str
    parent_id: str | None = Field(default=None, serialization_alias="parentId")
    type: str
    level: int
    leader: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    desc: str = ""
    employee_count: int = Field(default=0, serialization_alias="employeeCount")
    sort: int = 0
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")


# ── Response schemas (Department tree projection) ──────────────

class DepartmentTreeNode(CamelCaseModel):
    """Lightweight department node for the user management sidebar tree."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    parent_id: str | None = Field(default=None, serialization_alias="parentId")
    manager_id: str | None = Field(default=None, serialization_alias="managerId")
    description: str = ""
    member_count: int = Field(default=0, serialization_alias="memberCount")
    children: list["DepartmentTreeNode"] = Field(default_factory=list)
