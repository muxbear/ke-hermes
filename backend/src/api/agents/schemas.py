"""Request and response schemas for agent management."""
from datetime import datetime

from pydantic import BaseModel, Field

from agent.memory.scopes import MemoryScope


class AgentCreateRequest(BaseModel):
    """Request body for creating a new agent."""

    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    system_prompt: str = ""
    parent_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None


class AgentUpdateRequest(BaseModel):
    """Request body for updating an existing agent."""

    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    system_prompt: str = ""
    provider_id: str | None = None
    model_id: str | None = None


class AgentConfigRequest(BaseModel):
    """Request body for adding or removing a config item (tool / prompt / file / subagent)."""

    type: str  # tool | prompt | file | subagent (skill is handled separately)
    value: str
    description: str = ""
    scope: MemoryScope | None = None  # 仅 type=file 时生效；缺省按文件名推断


class AgentConfigUpdateRequest(BaseModel):
    """Request body for updating a config item (rename / change description)."""

    type: str  # tool | prompt | file
    value: str  # current name (用于定位要更新的项)
    new_value: str = ""  # 新文件名（空则不重命名）
    description: str = ""
    scope: MemoryScope | None = None  # 仅 type=file 时生效


class SkillBrief(BaseModel):
    """Brief skill info embedded in agent responses."""

    id: str
    name: str
    description: str
    category: str
    icon: str
    enabled: bool

    class Config:
        """Pydantic config for ORM model compatibility."""
        from_attributes = True


class AgentAddSkillRequest(BaseModel):
    """Request body for adding a skill to an agent."""

    skill_id: str = Field(..., min_length=1, description="Skill ID to add")


class FileBrief(BaseModel):
    """文件简要信息（按作用域分组返回）。"""

    filename: str
    scope: MemoryScope
    description: str = ""
    read_only: bool = False

    class Config:
        """Pydantic config for ORM model compatibility."""
        from_attributes = True


class AgentInfo(BaseModel):
    """Single agent record for list/detail responses."""

    id: str
    name: str
    type: str
    status: str
    description: str
    tools: list[str]
    skills: list[SkillBrief]
    system_prompt: str
    files: list[str]
    files_by_scope: dict[str, list[FileBrief]] = {}
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


class CronJobBrief(BaseModel):
    """Brief cron job info embedded in agent responses."""

    id: str
    agent_id: str
    name: str
    description: str
    cron_expression: str
    cron_label: str
    status: str
    target_type: str
    target: str
    last_run: datetime | None = None
    next_run: datetime | None = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """List of agents."""

    agents: list[AgentInfo]


class AgentFileContent(BaseModel):
    """File content record for an agent config file."""

    filename: str
    content: str
    description: str = ""
    scope: MemoryScope = MemoryScope.AGENT
    read_only: bool = False
    created_at: datetime | str
    updated_at: datetime | str

    class Config:
        """Pydantic config for ORM model compatibility."""
        from_attributes = True


class AgentFileUpdateRequest(BaseModel):
    """Request body for updating file content."""

    content: str
