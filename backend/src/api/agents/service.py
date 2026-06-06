"""Agent management business logic: CRUD, status toggle, clone, and config management."""
import logging

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.agents.schemas import (
    AgentConfigRequest,
    AgentConfigUpdateRequest,
    AgentCreateRequest,
    AgentFileContent,
    AgentInfo,
    AgentListResponse,
    AgentUpdateRequest,
)
from db.models.agent import Agent
from db.models.agent_file import AgentFile

logger = logging.getLogger(__name__)

CONFIG_TYPE_TO_COLUMN: dict[str, str] = {
    "tool": "tools",
    "skill": "skills",
    "prompt": "prompts",
    "file": "files",
}

DEFAULT_AGENT_FILES = [
    "AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md",
    "USER.md", "HEARTBEAT.md", "MEMORY.md",
]
DEFAULT_AGENT_TOOLS = ["web_search", "file_reader", "code_executor"]
DEFAULT_AGENT_SKILLS = ["code_analysis", "debugging", "optimization"]


async def _get_sub_agent_ids(db: AsyncSession, agent_id: str) -> list[str]:
    """Query for all agent IDs whose parent_id equals agent_id."""
    stmt = select(Agent.id).where(Agent.parent_id == agent_id)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


def _agent_to_info(agent: Agent, sub_agent_ids: list[str] | None = None) -> AgentInfo:
    """Convert ORM Agent to AgentInfo response schema."""
    return AgentInfo(
        id=agent.id,
        name=agent.name,
        type=agent.type,
        status=agent.status,
        description=agent.description,
        tools=agent.tools if isinstance(agent.tools, list) else [],
        skills=agent.skills if isinstance(agent.skills, list) else [],
        prompts=agent.prompts if isinstance(agent.prompts, list) else [],
        files=agent.files if isinstance(agent.files, list) else [],
        sub_agents=sub_agent_ids if sub_agent_ids is not None else [],
        parent_id=agent.parent_id,
        provider_id=agent.provider_id,
        model_id=agent.model_id,
        last_active=None,
        call_count=0,
        undeletable=agent.undeletable,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


async def list_agents(db: AsyncSession) -> AgentListResponse:
    """List all agents in the system, with computed sub_agents.

    If no agents exist yet, auto-creates a default main agent.
    """
    # Check if any agents exist; if not, seed a default main agent
    count = (await db.execute(
        select(func.count()).select_from(Agent)
    )).scalar() or 0
    if count == 0:
        agent = Agent(
            name="主智能体",
            type="main",
            status="active",
            description="负责整体任务协调和分发",
            tools=list(DEFAULT_AGENT_TOOLS),
            skills=list(DEFAULT_AGENT_SKILLS),
            files=list(DEFAULT_AGENT_FILES),
            undeletable=True,
        )
        db.add(agent)
        await db.flush()
        logger.info("Auto-created default main agent")

    stmt = select(Agent).order_by(Agent.type, Agent.created_at)
    rows = (await db.execute(stmt)).scalars().all()

    agents_info: list[AgentInfo] = []
    for agent in rows:
        sub_ids = await _get_sub_agent_ids(db, agent.id)
        agents_info.append(_agent_to_info(agent, sub_ids))

    return AgentListResponse(agents=agents_info)


async def get_agent(db: AsyncSession, agent_id: str) -> AgentInfo:
    """Get a single agent by ID."""
    stmt = select(Agent).where(Agent.id == agent_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    sub_ids = await _get_sub_agent_ids(db, agent_id)
    return _agent_to_info(row, sub_ids)


async def create_agent(db: AsyncSession, req: AgentCreateRequest) -> AgentInfo:
    """Create a new agent (main or sub)."""
    # Check name uniqueness globally
    existing = (await db.execute(
        select(Agent).where(Agent.name == req.name)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Agent name '{req.name}' already exists")

    agent = Agent(
        name=req.name,
        description=req.description or "",
        provider_id=req.provider_id,
        model_id=req.model_id,
    )

    if req.parent_id:
        # Creating a sub-agent — verify parent exists
        parent = (await db.execute(
            select(Agent).where(Agent.id == req.parent_id)
        )).scalar_one_or_none()
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent agent not found")
        agent.type = "sub"
        agent.parent_id = req.parent_id
    else:
        # Creating a main agent — only one in the system
        main_count = (await db.execute(
            select(func.count()).select_from(Agent).where(Agent.type == "main")
        )).scalar() or 0
        if main_count > 0:
            raise HTTPException(status_code=409, detail="Main agent already exists")
        agent.type = "main"

    db.add(agent)
    await db.flush()

    logger.info("Created agent '%s' (type=%s)", agent.name, agent.type)
    return _agent_to_info(agent, [])


async def delete_agent(db: AsyncSession, agent_id: str) -> None:
    """Delete an agent and cascade-delete sub-agents if it's a main agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.undeletable:
        raise HTTPException(status_code=403, detail="Agent is undeletable")

    if agent.type == "main":
        # Cascade-delete all sub-agents
        sub_stmt = select(Agent).where(Agent.parent_id == agent_id)
        sub_agents = (await db.execute(sub_stmt)).scalars().all()
        for sub in sub_agents:
            await db.delete(sub)
            logger.info("Cascade-deleted sub-agent '%s'", sub.name)

    await db.delete(agent)
    logger.info("Deleted agent '%s' (type=%s)", agent.name, agent.type)


async def toggle_agent_status(db: AsyncSession, agent_id: str) -> AgentInfo:
    """Toggle agent active/inactive status."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status == "active":
        agent.status = "inactive"
    elif agent.status == "error":
        agent.status = "inactive"
    else:
        agent.status = "active"

    sub_ids = await _get_sub_agent_ids(db, agent_id)
    return _agent_to_info(agent, sub_ids)


async def clone_agent(db: AsyncSession, agent_id: str) -> AgentInfo:
    """Clone an existing agent with a deduplicated name."""
    stmt = select(Agent).where(Agent.id == agent_id)
    source = (await db.execute(stmt)).scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Generate unique name: "原名 (副本)", "原名 (副本 2)", etc.
    base_name = f"{source.name} (副本)"
    new_name = base_name
    counter = 2
    while True:
        dup = (await db.execute(
            select(Agent).where(Agent.name == new_name)
        )).scalar_one_or_none()
        if dup is None:
            break
        new_name = f"{base_name} {counter}"
        counter += 1

    cloned = Agent(
        name=new_name,
        type=source.type,
        status="inactive",
        description=source.description,
        parent_id=source.parent_id,
        tools=list(source.tools) if isinstance(source.tools, list) else [],
        skills=list(source.skills) if isinstance(source.skills, list) else [],
        prompts=list(source.prompts) if isinstance(source.prompts, list) else [],
        files=list(source.files) if isinstance(source.files, list) else [],
        provider_id=source.provider_id,
        model_id=source.model_id,
        undeletable=False,
    )
    db.add(cloned)
    await db.flush()

    # Clone file contents
    src_files = source.files if isinstance(source.files, list) else []
    if src_files:
        src_contents_stmt = select(AgentFile).where(AgentFile.agent_id == agent_id)
        src_rows = (await db.execute(src_contents_stmt)).scalars().all()
        for src_row in src_rows:
            if src_row.filename in src_files:
                db.add(AgentFile(
                    agent_id=cloned.id,
                    filename=src_row.filename,
                    content=src_row.content,
                ))

    sub_ids = await _get_sub_agent_ids(db, cloned.id)
    logger.info("Cloned agent '%s' -> '%s'", source.name, cloned.name)
    return _agent_to_info(cloned, sub_ids)


async def update_agent(db: AsyncSession, agent_id: str, req: AgentUpdateRequest) -> AgentInfo:
    """Update an existing agent's name, description, and model assignment."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check name uniqueness (exclude self)
    dup = (await db.execute(
        select(Agent).where(Agent.name == req.name, Agent.id != agent_id)
    )).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status_code=409, detail=f"Agent name '{req.name}' already exists")

    agent.name = req.name
    agent.description = req.description
    agent.provider_id = req.provider_id
    agent.model_id = req.model_id

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    logger.info("Updated agent '%s'", agent.name)
    return _agent_to_info(agent, sub_ids)


async def add_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigRequest
) -> AgentInfo:
    """Add a config item (tool/skill/prompt/file/subagent) to an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.type == "subagent":
        # Sub-agents can only be added to main agents
        if agent.type != "main":
            raise HTTPException(status_code=400, detail="Only main agents can add sub-agents")
        sub_req = AgentCreateRequest(name=req.value, parent_id=agent_id)
        await create_agent(db, sub_req)
        await db.refresh(agent)
    else:
        column = CONFIG_TYPE_TO_COLUMN.get(req.type)
        if column is None:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {req.type}")
        current = getattr(agent, column)
        if not isinstance(current, list):
            current = []
        if req.value not in current:
            current = list(current)  # Create new list so SQLAlchemy detects change
            current.append(req.value)
            setattr(agent, column, current)

        # When adding a file, create an AgentFile record with description
        if req.type == "file" and req.description:
            existing = (await db.execute(
                select(AgentFile).where(
                    AgentFile.agent_id == agent_id, AgentFile.filename == req.value
                )
            )).scalar_one_or_none()
            if existing is not None:
                existing.description = req.description
            else:
                db.add(AgentFile(
                    agent_id=agent_id,
                    filename=req.value,
                    content="",
                    description=req.description,
                ))

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    return _agent_to_info(agent, sub_ids)


async def remove_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigRequest
) -> AgentInfo:
    """Remove a config item from an agent. For subagent type, deletes the sub-agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.type == "subagent":
        await delete_agent(db, req.value)
        await db.refresh(agent)
    else:
        column = CONFIG_TYPE_TO_COLUMN.get(req.type)
        if column is None:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {req.type}")
        current = getattr(agent, column)
        if isinstance(current, list) and req.value in current:
            current = [v for v in current if v != req.value]
            setattr(agent, column, current)
        # Clean up orphaned file content row when removing a file config
        if req.type == "file":
            del_stmt = delete(AgentFile).where(
                AgentFile.agent_id == agent_id, AgentFile.filename == req.value
            )
            await db.execute(del_stmt)

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    return _agent_to_info(agent, sub_ids)


async def update_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigUpdateRequest
) -> AgentInfo:
    """Update a config item (rename file / change description)."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    column = CONFIG_TYPE_TO_COLUMN.get(req.type)
    if column is None:
        raise HTTPException(status_code=400, detail=f"Invalid config type: {req.type}")

    current: list = getattr(agent, column)
    if not isinstance(current, list) or req.value not in current:
        raise HTTPException(status_code=404, detail=f"Config item '{req.value}' not found")

    if req.type == "file":
        new_name = req.new_value.strip() if req.new_value else ""
        # Rename file in agent.files
        if new_name and new_name != req.value:
            idx = current.index(req.value)
            current = list(current)
            current[idx] = new_name
            setattr(agent, column, current)

        # Update description in agent_files
        lookup_name = new_name if new_name else req.value
        file_stmt = select(AgentFile).where(
            AgentFile.agent_id == agent_id, AgentFile.filename == req.value
        )
        row = (await db.execute(file_stmt)).scalar_one_or_none()
        if row is not None:
            if new_name and new_name != req.value:
                row.filename = new_name
            row.description = req.description
        elif req.description:
            db.add(AgentFile(
                agent_id=agent_id,
                filename=lookup_name,
                content="",
                description=req.description,
            ))

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    return _agent_to_info(agent, sub_ids)


async def get_agent_file(
    db: AsyncSession, agent_id: str, filename: str
) -> AgentFileContent:
    """Get file content for a given agent and filename. Auto-creates empty record on first access."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []
    if filename not in files:
        raise HTTPException(status_code=404, detail="File not found in agent config")

    file_stmt = select(AgentFile).where(
        AgentFile.agent_id == agent_id, AgentFile.filename == filename
    )
    row = (await db.execute(file_stmt)).scalar_one_or_none()
    if row is None:
        row = AgentFile(agent_id=agent_id, filename=filename, content="")
        db.add(row)
        await db.flush()

    return AgentFileContent(
        filename=row.filename,
        content=row.content or "",
        description=row.description or "",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def save_agent_file(
    db: AsyncSession, agent_id: str, filename: str, content: str
) -> AgentFileContent:
    """Save file content for a given agent and filename (upsert)."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []
    if filename not in files:
        raise HTTPException(status_code=404, detail="File not found in agent config")

    file_stmt = select(AgentFile).where(
        AgentFile.agent_id == agent_id, AgentFile.filename == filename
    )
    row = (await db.execute(file_stmt)).scalar_one_or_none()
    if row is None:
        row = AgentFile(agent_id=agent_id, filename=filename, content=content)
        db.add(row)
    else:
        row.content = content

    await db.flush()
    return AgentFileContent(
        filename=row.filename,
        content=row.content or "",
        description=row.description or "",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def list_agent_file_descriptions(
    db: AsyncSession, agent_id: str
) -> list[dict]:
    """Return {filename, description} for all files of an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    file_stmt = select(AgentFile).where(AgentFile.agent_id == agent_id)
    rows = (await db.execute(file_stmt)).scalars().all()
    return [{"filename": row.filename, "description": row.description or ""} for row in rows]
