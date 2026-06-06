"""Request and response schemas for agent management."""
from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    """Request body for creating a new agent."""

    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    parent_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None


class AgentUpdateRequest(BaseModel):
    """Request body for updating an existing agent."""

    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    provider_id: str | None = None
    model_id: str | None = None


class AgentConfigRequest(BaseModel):
    """Request body for adding or removing a config item."""

    type: str  # tool | skill | prompt | file | subagent
    value: str
    description: str = ""


class AgentInfo(BaseModel):
    """Single agent record for list/detail responses."""

    id: str
    name: str
    type: str
    status: str
    description: str
    tools: list[str]
    skills: list[str]
    prompts: list[str]
    files: list[str]
    sub_agents: list[str] = []
    parent_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    last_active: str | None = None
    call_count: int = 0
    undeletable: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM model compatibility."""
        from_attributes = True


class AgentListResponse(BaseModel):
    """List of agents."""

    agents: list[AgentInfo]


class AgentFileContent(BaseModel):
    """File content record for an agent config file."""

    filename: str
    content: str
    description: str = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM model compatibility."""
        from_attributes = True


class AgentFileUpdateRequest(BaseModel):
    """Request body for updating file content."""

    content: str


class AgentConfigUpdateRequest(BaseModel):
    """Request body for updating a config item (rename / change description)."""

    type: str  # tool | skill | prompt | file
    value: str  # current name (用于定位要更新的项)
    new_value: str = ""  # 新文件名（空则不重命名）
    description: str = ""
