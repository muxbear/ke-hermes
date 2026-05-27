"""Request and response schemas for MCP marketplace API."""

from datetime import datetime

from pydantic import BaseModel


class McpConfigFieldSchema(BaseModel):
    """Schema for a single MCP tool config field definition."""

    name: str
    label: str
    type: str
    required: bool = False
    default: str | int | float | bool | None = None
    options: list[str] | None = None
    description: str | None = None


class McpToolResponse(BaseModel):
    """Single MCP tool for list/detail responses."""

    id: str
    name: str
    description: str
    icon: str
    author: str
    version: str
    license: str
    repository: str
    installs: int = 0
    rating: float = 0.0
    category: str
    tags: list[str] = []
    features: list[str] = []
    official: bool = False
    installed: bool = False
    config_schema: list[McpConfigFieldSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM model compatibility."""

        from_attributes = True


class InstallMcpRequest(BaseModel):
    """Request body for installing an MCP tool."""

    mcp_id: str
    config: dict[str, str | int | float | bool] | None = None
