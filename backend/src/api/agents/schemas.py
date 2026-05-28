"""Request and response schemas for agent management."""
from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    """Request body for creating a new agent."""

    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    parent_id: str | None = None


class AgentConfigRequest(BaseModel):
    """Request body for adding or removing a config item."""

    type: str  # tool | skill | prompt | file | subagent
    value: str


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
