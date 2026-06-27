"""Agent management business logic: CRUD, status toggle, clone, and config management."""
import logging
import os
import shutil

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import get_store
from agent.memory.memory_sync import (
    delete_agent_file_from_store,
    sync_agent_file_to_store,
)
from agent.memory.scopes import (
    DEFAULT_ORG_ID,
    TEMPLATE_USER_ID,
    MemoryScope,
    infer_scope,
)
from api.agents.schemas import (
    AgentAddSkillRequest,
    AgentConfigRequest,
    AgentConfigUpdateRequest,
    AgentCreateRequest,
    AgentFileContent,
    AgentInfo,
    AgentListResponse,
    AgentUpdateRequest,
    CronJobBrief,
    FileBrief,
    SkillBrief,
)
from db.models.agent import Agent
from db.models.agent_file import AgentFile
from db.models.agent_skill import AgentSkill
from db.models.agent_tool import AgentTool
from db.models.cron_job import CronJob
from db.models.skill import Skill
from db.models.tool import Tool

from agent.config import settings
from api.skill.service import get_skill_upload_path

logger = logging.getLogger(__name__)

CONFIG_TYPE_TO_COLUMN: dict[str, str] = {
    "file": "files",
}

DEFAULT_AGENT_FILES = [
    "AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md",
    "USER.md", "HEARTBEAT.md", "MEMORY.md",
]

DEFAULT_AGENT_TOOLS = ["http_request"]


async def _get_agent_files_by_scope(
    db: AsyncSession, agent_id: str, files: list[str]
) -> dict[str, list[FileBrief]]:
    """查询 AgentFile 表，按 scope 分组返回 FileBrief。"""
    if not files:
        return {s.value: [] for s in MemoryScope}

    stmt = select(AgentFile).where(
        AgentFile.agent_id == agent_id, AgentFile.filename.in_(files)
    )
    rows = (await db.execute(stmt)).scalars().all()
    brief_by_filename: dict[str, FileBrief] = {}
    for row in rows:
        try:
            scope = MemoryScope(row.scope) if row.scope else infer_scope(row.filename)
        except ValueError:
            scope = infer_scope(row.filename)
        brief_by_filename[row.filename] = FileBrief(
            filename=row.filename,
            scope=scope,
            description=row.description or "",
            read_only=bool(row.read_only),
        )

    # 对未在表中找到记录的文件，按文件名推断 scope
    for f in files:
        if f not in brief_by_filename:
            scope = infer_scope(f)
            brief_by_filename[f] = FileBrief(
                filename=f,
                scope=scope,
                description="",
                read_only=(scope is MemoryScope.ORG),
            )

    grouped: dict[str, list[FileBrief]] = {s.value: [] for s in MemoryScope}
    for f in files:
        brief = brief_by_filename[f]
        grouped[brief.scope.value].append(brief)
    return grouped


async def _sync_file_to_store(
    agent_id: str,
    filename: str,
    content: str,
    scope: MemoryScope,
    org_id: str | None = None,
) -> None:
    """将文件内容同步到 LangGraph Store。失败仅记录日志，不影响 DB 事务。"""
    try:
        store = get_store()
    except RuntimeError:
        logger.warning("Store 未初始化，跳过文件 %s 的同步", filename)
        return

    try:
        await sync_agent_file_to_store(
            store,
            agent_id=agent_id,
            user_id=TEMPLATE_USER_ID,
            org_id=org_id or DEFAULT_ORG_ID,
            filename=filename,
            content=content,
            scope=scope,
        )
    except Exception:
        logger.exception("同步文件 %s (scope=%s) 到 Store 失败", filename, scope.value)


async def _get_sub_agent_ids(db: AsyncSession, agent_id: str) -> list[str]:
    """Query for all agent IDs whose parent_id equals agent_id."""
    stmt = select(Agent.id).where(Agent.parent_id == agent_id)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


async def _get_agent_skill_briefs(db: AsyncSession, agent_id: str) -> list[SkillBrief]:
    """Query skills linked to an agent via the agent_skills junction table."""
    stmt = (
        select(Skill)
        .join(AgentSkill, AgentSkill.skill_id == Skill.id)
        .where(AgentSkill.agent_id == agent_id)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        SkillBrief(
            id=s.id,
            name=s.name,
            description=s.description,
            category=s.category,
            icon=s.icon,
            enabled=s.enabled,
        )
        for s in rows
    ]


async def _get_agent_tool_names(db: AsyncSession, agent_id: str) -> list[str]:
    """Query tool names linked to an agent via the agent_tools junction table."""
    stmt = (
        select(Tool.name)
        .join(AgentTool, AgentTool.tool_id == Tool.id)
        .where(AgentTool.agent_id == agent_id)
        .order_by(Tool.name)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


async def _agent_to_info(
    db: AsyncSession,
    agent: Agent,
    sub_agent_ids: list[str] | None = None,
    skills: list[SkillBrief] | None = None,
    tool_names: list[str] | None = None,
) -> AgentInfo:
    """Convert ORM Agent to AgentInfo response schema."""
    files = agent.files if isinstance(agent.files, list) else []
    files_by_scope = await _get_agent_files_by_scope(db, agent.id, files)
    return AgentInfo(
        id=agent.id,
        name=agent.name,
        type=agent.type,
        status=agent.status,
        description=agent.description,
        tools=tool_names if tool_names is not None else [],
        skills=skills if skills is not None else [],
        system_prompt=agent.system_prompt or "",
        files=files,
        files_by_scope=files_by_scope,
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
        logger.warning("智能体菜单中当前没有配置主智能体，系统采用默认配置创建了主智能体，请登录系统后重新配置！")
        agent = Agent(
            name="主智能体",
            type="main",
            status="active",
            description="负责整体任务协调和分发",
            files=list(DEFAULT_AGENT_FILES),
            undeletable=True,
        )
        db.add(agent)
        await db.flush()

        # Create tool links for default agent
        for tool_name in DEFAULT_AGENT_TOOLS:
            tool = (await db.execute(
                select(Tool).where(Tool.name == tool_name)
            )).scalar_one_or_none()
            if tool is not None:
                db.add(AgentTool(agent_id=agent.id, tool_id=tool.id))
            else:
                logger.warning("Default tool '%s' not found, skipping", tool_name)

        logger.info("Auto-created default main agent")

    stmt = select(Agent).order_by(Agent.type, Agent.created_at)
    rows = (await db.execute(stmt)).scalars().all()

    agents_info: list[AgentInfo] = []
    for agent in rows:
        sub_ids = await _get_sub_agent_ids(db, agent.id)
        skills = await _get_agent_skill_briefs(db, agent.id)
        tool_names = await _get_agent_tool_names(db, agent.id)
        agents_info.append(await _agent_to_info(db, agent, sub_ids, skills, tool_names))

    return AgentListResponse(agents=agents_info)


async def get_agent(db: AsyncSession, agent_id: str) -> AgentInfo:
    """Get a single agent by ID."""
    stmt = select(Agent).where(Agent.id == agent_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, row, sub_ids, skills, tool_names)


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
        system_prompt=req.system_prompt or "",
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
    return await _agent_to_info(db, agent, [])


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
            _cleanup_agent_skills_dir(sub.id)
            logger.info("Cascade-deleted sub-agent '%s'", sub.name)

    await db.delete(agent)
    _cleanup_agent_skills_dir(agent_id)
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
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


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
        system_prompt=source.system_prompt or "",
        files=list(source.files) if isinstance(source.files, list) else [],
        provider_id=source.provider_id,
        model_id=source.model_id,
        undeletable=False,
    )
    db.add(cloned)
    await db.flush()

    # Clone agent_tools associations
    tool_link_stmt = select(AgentTool).where(AgentTool.agent_id == agent_id)
    tool_links = (await db.execute(tool_link_stmt)).scalars().all()
    for link in tool_links:
        db.add(AgentTool(agent_id=cloned.id, tool_id=link.tool_id))

    # Clone agent_skills associations
    skill_stmt = select(AgentSkill).where(AgentSkill.agent_id == agent_id)
    skill_links = (await db.execute(skill_stmt)).scalars().all()
    for link in skill_links:
        db.add(AgentSkill(agent_id=cloned.id, skill_id=link.skill_id))

    # Clone skill filesystem directories
    if skill_links:
        skill_ids = [link.skill_id for link in skill_links]
        skill_rows = (await db.execute(
            select(Skill).where(Skill.id.in_(skill_ids))
        )).scalars().all()
        for skill in skill_rows:
            src = _agent_skill_dir(agent_id, skill.name)
            dst = _agent_skill_dir(cloned.id, skill.name)
            if os.path.isdir(src):
                os.makedirs(_agent_skills_dir(cloned.id), exist_ok=True)
                shutil.copytree(src, dst)
                logger.info(
                    "Copied skill '%s' from agent '%s' to '%s'",
                    skill.name, agent_id, cloned.id,
                )

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
    skills = await _get_agent_skill_briefs(db, cloned.id)
    tool_names = await _get_agent_tool_names(db, cloned.id)
    logger.info("Cloned agent '%s' -> '%s'", source.name, cloned.name)
    return await _agent_to_info(db, cloned, sub_ids, skills, tool_names)


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
    agent.system_prompt = req.system_prompt
    agent.provider_id = req.provider_id
    agent.model_id = req.model_id

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    logger.info("Updated agent '%s'", agent.name)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


async def add_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigRequest
) -> AgentInfo:
    """Add a config item (tool/prompt/file/subagent) to an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.type == "tool":
        tool = (await db.execute(
            select(Tool).where(Tool.name == req.value)
        )).scalar_one_or_none()
        if tool is None:
            raise HTTPException(status_code=404, detail=f"工具 '{req.value}' 不存在")
        existing = (await db.execute(
            select(AgentTool).where(
                AgentTool.agent_id == agent_id, AgentTool.tool_id == tool.id
            )
        )).scalar_one_or_none()
        if existing is None:
            db.add(AgentTool(agent_id=agent_id, tool_id=tool.id))
    elif req.type == "subagent":
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

        # When adding a file, create an AgentFile record with description + scope
        if req.type == "file":
            scope = req.scope or infer_scope(req.value)
            if scope is MemoryScope.ORG:
                raise HTTPException(
                    status_code=400,
                    detail="组织级文件请走专用 /policies/ 接口",
                )
            existing = (await db.execute(
                select(AgentFile).where(
                    AgentFile.agent_id == agent_id,
                    AgentFile.filename == req.value,
                    AgentFile.scope == scope.value,
                )
            )).scalar_one_or_none()
            if existing is not None:
                if req.description:
                    existing.description = req.description
            else:
                db.add(AgentFile(
                    agent_id=agent_id,
                    filename=req.value,
                    content="",
                    description=req.description,
                    scope=scope.value,
                    read_only=False,
                ))
                await db.flush()
                # 同步空种子到 Store
                await _sync_file_to_store(
                    agent_id, req.value, "", scope
                )

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


async def remove_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigRequest
) -> AgentInfo:
    """Remove a config item from an agent. For subagent type, deletes the sub-agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.type == "tool":
        tool = (await db.execute(
            select(Tool).where(Tool.name == req.value)
        )).scalar_one_or_none()
        if tool is None:
            raise HTTPException(status_code=404, detail=f"工具 '{req.value}' 不存在")
        link = (await db.execute(
            select(AgentTool).where(
                AgentTool.agent_id == agent_id, AgentTool.tool_id == tool.id
            )
        )).scalar_one_or_none()
        if link is not None:
            await db.delete(link)
    elif req.type == "subagent":
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
            scope = req.scope or infer_scope(req.value)
            # 删除所有 scope 下的同名文件（保险起见）
            del_stmt = delete(AgentFile).where(
                AgentFile.agent_id == agent_id, AgentFile.filename == req.value
            )
            await db.execute(del_stmt)
            # 从 Store 删除
            try:
                store = get_store()
                await delete_agent_file_from_store(
                    store,
                    agent_id=agent_id,
                    user_id=TEMPLATE_USER_ID,
                    org_id=DEFAULT_ORG_ID,
                    filename=req.value,
                    scope=scope,
                )
            except Exception:
                logger.warning(
                    "从 Store 删除文件 %s 失败", req.value, exc_info=True
                )

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


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
        scope = req.scope or infer_scope(req.value)
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
            AgentFile.agent_id == agent_id,
            AgentFile.filename == req.value,
            AgentFile.scope == scope.value,
        )
        row = (await db.execute(file_stmt)).scalar_one_or_none()
        if row is not None:
            if new_name and new_name != req.value:
                row.filename = new_name
            row.description = req.description
            content = row.content or ""
            new_scope = req.scope or infer_scope(lookup_name)
            row.scope = new_scope.value
            await db.flush()
            await _sync_file_to_store(agent_id, lookup_name, content, new_scope)
        elif req.description:
            new_scope = req.scope or infer_scope(lookup_name)
            db.add(AgentFile(
                agent_id=agent_id,
                filename=lookup_name,
                content="",
                description=req.description,
                scope=new_scope.value,
            ))

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


async def get_agent_file(
    db: AsyncSession,
    agent_id: str,
    filename: str,
    scope: MemoryScope | None = None,
) -> AgentFileContent:
    """Get file content for a given agent and filename. Auto-creates empty record on first access."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []
    if filename not in files:
        raise HTTPException(status_code=404, detail="File not found in agent config")

    resolved_scope = scope or infer_scope(filename)
    file_stmt = select(AgentFile).where(
        AgentFile.agent_id == agent_id,
        AgentFile.filename == filename,
        AgentFile.scope == resolved_scope.value,
    )
    row = (await db.execute(file_stmt)).scalar_one_or_none()
    if row is None:
        # 兜底：查找任意 scope 下的同名文件
        fallback_stmt = select(AgentFile).where(
            AgentFile.agent_id == agent_id, AgentFile.filename == filename
        )
        row = (await db.execute(fallback_stmt)).scalar_one_or_none()
    if row is None:
        row = AgentFile(
            agent_id=agent_id,
            filename=filename,
            content="",
            scope=resolved_scope.value,
            read_only=(resolved_scope is MemoryScope.ORG),
        )
        db.add(row)
        await db.flush()

    try:
        row_scope = MemoryScope(row.scope) if row.scope else resolved_scope
    except ValueError:
        row_scope = resolved_scope

    return AgentFileContent(
        filename=row.filename,
        content=row.content or "",
        description=row.description or "",
        scope=row_scope,
        read_only=bool(row.read_only) or row_scope is MemoryScope.ORG,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def save_agent_file(
    db: AsyncSession,
    agent_id: str,
    filename: str,
    content: str,
    scope: MemoryScope | None = None,
) -> AgentFileContent:
    """Save file content for a given agent and filename (upsert)."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []
    if filename not in files:
        raise HTTPException(status_code=404, detail="File not found in agent config")

    resolved_scope = scope or infer_scope(filename)
    if resolved_scope is MemoryScope.ORG:
        raise HTTPException(
            status_code=403,
            detail="组织级只读文件不可通过此接口修改，请走 /policies/ 接口",
        )

    file_stmt = select(AgentFile).where(
        AgentFile.agent_id == agent_id,
        AgentFile.filename == filename,
        AgentFile.scope == resolved_scope.value,
    )
    row = (await db.execute(file_stmt)).scalar_one_or_none()
    if row is None:
        row = AgentFile(
            agent_id=agent_id,
            filename=filename,
            content=content,
            scope=resolved_scope.value,
            read_only=False,
        )
        db.add(row)
    else:
        row.content = content
        row.scope = resolved_scope.value

    await db.flush()
    # 同步到 Store
    await _sync_file_to_store(agent_id, filename, content, resolved_scope)

    return AgentFileContent(
        filename=row.filename,
        content=row.content or "",
        description=row.description or "",
        scope=resolved_scope,
        read_only=False,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def list_agent_file_descriptions(
    db: AsyncSession, agent_id: str
) -> list[dict]:
    """Return {filename, description, scope, readOnly} for all files of an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    file_stmt = select(AgentFile).where(AgentFile.agent_id == agent_id)
    rows = (await db.execute(file_stmt)).scalars().all()
    return [
        {
            "filename": row.filename,
            "description": row.description or "",
            "scope": row.scope or infer_scope(row.filename).value,
            "readOnly": bool(row.read_only),
        }
        for row in rows
    ]


# ── Agent-Skill helpers ───────────────────────────────────────────────────


SKILLS_ROOT = os.path.join(settings.WORKSPACE, "skills")


def _agent_skills_dir(agent_id: str) -> str:
    """Return the filesystem path for an agent's skills directory."""
    return os.path.join(SKILLS_ROOT, agent_id)


def _agent_skill_dir(agent_id: str, skill_name: str) -> str:
    """Return the filesystem path for a specific skill under an agent."""
    return os.path.join(_agent_skills_dir(agent_id), skill_name)


def _cleanup_agent_skills_dir(agent_id: str) -> None:
    """Remove the entire skills directory for an agent."""
    agent_dir = _agent_skills_dir(agent_id)
    if os.path.isdir(agent_dir):
        shutil.rmtree(agent_dir, ignore_errors=True)
        logger.info("Removed skills directory for agent '%s': %s", agent_id, agent_dir)


# ── Agent-Skill relationship ──────────────────────────────────────────────


async def get_agent_skills(
    db: AsyncSession, agent_id: str
) -> list[SkillBrief]:
    """Get all skills linked to an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await _get_agent_skill_briefs(db, agent_id)


async def add_skill_to_agent(
    db: AsyncSession, agent_id: str, req: AgentAddSkillRequest
) -> list[SkillBrief]:
    """Add a skill to an agent via the junction table."""
    # Verify agent exists
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Verify skill exists
    skill_stmt = select(Skill).where(Skill.id == req.skill_id)
    skill = (await db.execute(skill_stmt)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Check for duplicate
    dup_stmt = select(AgentSkill).where(
        AgentSkill.agent_id == agent_id, AgentSkill.skill_id == req.skill_id
    )
    dup = (await db.execute(dup_stmt)).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status_code=409, detail="Skill already added to this agent")

    # Copy skill from catalog to agent's skills directory
    skill_upload_path = get_skill_upload_path(skill.name)
    agent_skill_dest = _agent_skill_dir(agent_id, skill.name)

    if not os.path.isdir(skill_upload_path):
        raise HTTPException(
            status_code=500,
            detail=f"Skill package not found on disk: {skill_upload_path}",
        )

    os.makedirs(_agent_skills_dir(agent_id), exist_ok=True)
    if not os.path.isdir(agent_skill_dest):
        shutil.copytree(skill_upload_path, agent_skill_dest)
        logger.info("Copied skill '%s' to agent '%s' at '%s'", skill.name, agent.name, agent_skill_dest)

    db.add(AgentSkill(agent_id=agent_id, skill_id=req.skill_id))
    await db.flush()
    logger.info("Added skill '%s' to agent '%s'", skill.name, agent.name)

    return await _get_agent_skill_briefs(db, agent_id)


async def remove_skill_from_agent(
    db: AsyncSession, agent_id: str, skill_id: str
) -> None:
    """Remove a skill from an agent — DB record and filesystem directory."""
    stmt = select(AgentSkill).where(
        AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id
    )
    link = (await db.execute(stmt)).scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Skill not found on this agent")

    # Resolve skill name for filesystem cleanup
    skill_stmt = select(Skill).where(Skill.id == skill_id)
    skill = (await db.execute(skill_stmt)).scalar_one_or_none()

    await db.delete(link)
    await db.flush()
    logger.info("Removed skill '%s' from agent '%s'", skill_id, agent_id)

    if skill is not None:
        agent_skill_path = _agent_skill_dir(agent_id, skill.name)
        if os.path.isdir(agent_skill_path):
            shutil.rmtree(agent_skill_path, ignore_errors=True)
            logger.info(
                "Deleted skill directory '%s' for agent '%s'",
                agent_skill_path, agent_id,
            )


# ── Agent-CronJob relationship ────────────────────────────────────────────


async def get_agent_cron_jobs(db: AsyncSession, agent_id: str) -> list[CronJobBrief]:
    """Get all cron jobs belonging to an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    cron_stmt = select(CronJob).where(CronJob.agent_id == agent_id).order_by(CronJob.created_at)
    rows = (await db.execute(cron_stmt)).scalars().all()
    return [
        CronJobBrief(
            id=cj.id,
            agent_id=cj.agent_id,
            name=cj.name,
            description=cj.description,
            cron_expression=cj.cron_expression,
            cron_label=cj.cron_label,
            status=cj.status,
            target_type=cj.target_type,
            target=cj.target,
            last_run=cj.last_run,
            next_run=cj.next_run,
            tags=cj.tags if isinstance(cj.tags, list) else [],
            created_at=cj.created_at,
            updated_at=cj.updated_at,
        )
        for cj in rows
    ]
