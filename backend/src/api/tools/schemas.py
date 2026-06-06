"""Request and response schemas for tool management."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ToolParam(BaseModel):
    """Parameter definition for a tool."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    key: str
    label: str
    required: bool = False
    type: str = "string"


class ToolInfo(BaseModel):
    """Single tool record for list/detail responses."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    display_name: str
    description: str
    category: str
    source: str
    status: str
    version: str
    author: str
    used_by_agents: list[str] = []
    tags: list[str] = []
    params: list[ToolParam] = []
    created_at: datetime
    updated_at: datetime


class ToolListResponse(BaseModel):
    """Paginated list of tools."""

    items: list[ToolInfo]
    total: int
    page: int
    page_size: int


class ToolCreateRequest(BaseModel):
    """Request body for creating a third-party tool."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    display_name: str
    description: str = ""
    category: str = "other"
    status: str = "enabled"
    version: str = "1.0.0"
    tags: list[str] = []
    params: list[ToolParam] = []


class ToolUpdateRequest(BaseModel):
    """Request body for updating a tool."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    version: str | None = None
    tags: list[str] | None = None
    params: list[ToolParam] | None = None


class ToolToggleRequest(BaseModel):
    """Request body for toggling tool status."""

    enabled: bool


