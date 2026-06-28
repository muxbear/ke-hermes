"""Agent management business logic: CRUD, status toggle, clone, and config management."""
import logging
import os
import shutil

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import get_store
from agent.memory.scopes import (
    DEFAULT_ORG_ID,
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
    """从 LangGraph Store 读取文件元数据，按 scope 分组返回 FileBrief。"""
    if not files:
        return {s.value: [] for s in MemoryScope}

    from agent.graph import get_store

    try:
        store = get_store()
    except RuntimeError:
        store = None

    briefs: list[FileBrief] = []
    for filename in files:
        scope = infer_scope(filename)
        description = ""
        read_only = (scope is MemoryScope.ORG)

        if store is not None:
            # 遍历所有非 ORG 作用域的 namespace 查找文件，
            # 因为 add_agent_config() 写入的 scope 可能与 infer_scope() 推断不同
            item = None
            for candidate_scope in (MemoryScope.AGENT, MemoryScope.USER, MemoryScope.MIXTURE):
                try:
                    candidate_ns = _file_namespace(candidate_scope, agent_id=agent_id)
                    item = await store.aget(candidate_ns, f"/{filename}")
                    if item is not None:
                        scope = candidate_scope
                        break
                except Exception:
                    continue

            if item is not None:
                meta = _extract_file_metadata(item.value)
                description = str(meta["description"])
                read_only = bool(meta["read_only"])
                # stored scope 优先（处理同一文件在多个 namespace 的情况）
                stored_scope = str(meta.get("scope", ""))
                if stored_scope:
                    try:
                        scope = MemoryScope(stored_scope)
                    except ValueError:
                        pass

        briefs.append(FileBrief(
            filename=filename,
            scope=scope,
            description=description,
            read_only=read_only,
        ))

    grouped: dict[str, list[FileBrief]] = {s.value: [] for s in MemoryScope}
    for brief in briefs:
        grouped[brief.scope.value].append(brief)
    return grouped


def _file_namespace(scope: MemoryScope, *, agent_id: str, user_id: str | None = None, org_id: str | None = None) -> tuple[str, ...]:
    """返回文件作用域对应的 Store namespace（不区分模板/用户）。"""
    from agent.memory.scopes import DEFAULT_ORG_ID, scope_namespace
    return scope_namespace(
        scope, agent_id=agent_id, user_id=user_id, org_id=org_id or DEFAULT_ORG_ID,
    )


def _extract_file_metadata(value: object) -> dict[str, str | bool | None]:
    """从 Store value 提取文件元数据，缺失时返回默认值。"""
    from agent.memory.file_data import file_value_to_metadata
    metadata = file_value_to_metadata(value)
    return {
        "description": str(metadata.get("description", "")),
        "scope": str(metadata.get("scope", "agent")),
        "read_only": bool(metadata.get("read_only", False)),
        "org_id": str(metadata["org_id"]) if metadata.get("org_id") else None,
    }


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

    # Clone file contents from Store
    src_files = source.files if isinstance(source.files, list) else []
    if src_files:
        try:
            store = get_store()
        except RuntimeError:
            store = None
        if store is not None:
            for f in src_files:
                scope = infer_scope(f)
                src_ns = _file_namespace(scope, agent_id=agent_id)
                dst_ns = _file_namespace(scope, agent_id=cloned.id)
                try:
                    item = await store.aget(src_ns, f"/{f}")
                    if item is not None and item.value is not None:
                        await store.aput(dst_ns, f"/{f}", item.value)
                except Exception:
                    logger.warning("克隆文件 %s 到新 agent %s 失败", f, cloned.id, exc_info=True)

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
    db: AsyncSession, agent_id: str, req: AgentConfigRequest, *, user_id: str | None = None,
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

        # 添加文件时写入空种子到 Store
        if req.type == "file":
            scope = req.scope or infer_scope(req.value)
            if scope is MemoryScope.ORG:
                raise HTTPException(
                    status_code=400,
                    detail="组织级文件请走专用 /policies/ 接口",
                )
            # 写入空种子到 Store（USER/MIXTURE 使用实际 user_id）
            try:
                store = get_store()
                ns_user_id = user_id if scope in (MemoryScope.USER, MemoryScope.MIXTURE) else None
                namespace = _file_namespace(scope, agent_id=agent_id, user_id=ns_user_id)
                existing = await store.aget(namespace, f"/{req.value}")
                if existing is None:
                    from agent.memory.file_data import create_agent_file_data
                    value = create_agent_file_data(
                        content="", description=req.description, scope=scope,
                    )
                    await store.aput(namespace, f"/{req.value}", value)
            except RuntimeError:
                pass

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


async def remove_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigRequest, *, user_id: str | None = None,
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
        # 从 Store 删除文件
        if req.type == "file":
            try:
                store = get_store()
                scope = req.scope or infer_scope(req.value)
                ns_user_id = user_id if scope in (MemoryScope.USER, MemoryScope.MIXTURE) else None
                namespace = _file_namespace(scope, agent_id=agent_id, user_id=ns_user_id)
                await store.adelete(namespace, f"/{req.value}")
            except RuntimeError:
                pass
            except Exception:
                logger.warning("从 Store 删除文件 %s 失败", req.value, exc_info=True)

    await db.flush()
    sub_ids = await _get_sub_agent_ids(db, agent_id)
    skills = await _get_agent_skill_briefs(db, agent_id)
    tool_names = await _get_agent_tool_names(db, agent_id)
    return await _agent_to_info(db, agent, sub_ids, skills, tool_names)


async def update_agent_config(
    db: AsyncSession, agent_id: str, req: AgentConfigUpdateRequest, *, user_id: str | None = None,
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

        # 在 Store 中重命名或更新描述
        lookup_name = new_name if new_name else req.value
        try:
            store = get_store()
            ns_user_id = user_id if scope in (MemoryScope.USER, MemoryScope.MIXTURE) else None
            namespace = _file_namespace(scope, agent_id=agent_id, user_id=ns_user_id)
            item = await store.aget(namespace, f"/{req.value}")
            if item is not None:
                value = dict(item.value) if isinstance(item.value, dict) else {}
                if req.description:
                    value["description"] = req.description
                if new_name and new_name != req.value:
                    # 复制到新 key，删除旧 key
                    await store.aput(namespace, f"/{new_name}", value)
                    await store.adelete(namespace, f"/{req.value}")
                else:
                    await store.aput(namespace, f"/{req.value}", value)
        except RuntimeError:
            pass

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
    *,
    user_id: str | None = None,
) -> AgentFileContent:
    """从 LangGraph Store 读取文件内容。不存在时返回空内容 + 默认元数据。"""
    from agent.memory.file_data import file_value_to_agent_file_content

    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []
    if filename not in files:
        raise HTTPException(status_code=404, detail="File not found in agent config")

    resolved_scope = scope or infer_scope(filename)

    try:
        store = get_store()
    except RuntimeError:
        store = None

    value = None
    found_scope = resolved_scope
    if store is not None:
        # 遍历所有非 ORG 作用域查找文件
        for candidate_scope in (MemoryScope.AGENT, MemoryScope.USER, MemoryScope.MIXTURE):
            try:
                ns_user_id = user_id if candidate_scope in (MemoryScope.USER, MemoryScope.MIXTURE) else None
                candidate_ns = _file_namespace(candidate_scope, agent_id=agent_id, user_id=ns_user_id)
                item = await store.aget(candidate_ns, f"/{filename}")
                if item is not None:
                    value = item.value
                    found_scope = candidate_scope
                    break
            except Exception:
                continue

    result = file_value_to_agent_file_content(value, filename, default_scope=found_scope)
    return AgentFileContent(**result)


async def save_agent_file(
    db: AsyncSession,
    agent_id: str,
    filename: str,
    content: str,
    scope: MemoryScope | None = None,
    *,
    user_id: str | None = None,
) -> AgentFileContent:
    """将文件内容直接写入 LangGraph Store（upsert）。"""
    from agent.memory.file_data import create_agent_file_data, file_value_to_agent_file_content, file_value_to_content

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

    value = create_agent_file_data(
        content=content, description="", scope=resolved_scope, read_only=False,
    )

    try:
        store = get_store()
        ns_user_id = user_id if resolved_scope in (MemoryScope.USER, MemoryScope.MIXTURE) else None
        namespace = _file_namespace(resolved_scope, agent_id=agent_id, user_id=ns_user_id)
        await store.aput(namespace, f"/{filename}", value)
    except RuntimeError:
        logger.warning("Store 未初始化，文件 %s 仅写入内存", filename)
    except Exception:
        logger.exception("写入文件 %s 到 Store 失败", filename)

    result = file_value_to_agent_file_content(value, filename, default_scope=resolved_scope)
    return AgentFileContent(**result)


async def list_agent_file_descriptions(
    db: AsyncSession, agent_id: str
) -> list[dict]:
    """从 agents.files 清单 + Store 元数据返回文件描述列表。"""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []

    try:
        store = get_store()
    except RuntimeError:
        store = None

    result = []
    for f in files:
        scope = infer_scope(f)
        description = ""
        read_only = (scope is MemoryScope.ORG)
        if store is not None:
            # 遍历所有非 ORG 作用域查找文件
            for candidate_scope in (MemoryScope.AGENT, MemoryScope.USER, MemoryScope.MIXTURE):
                try:
                    candidate_ns = _file_namespace(candidate_scope, agent_id=agent_id)
                    item = await store.aget(candidate_ns, f"/{f}")
                    if item is not None:
                        meta = _extract_file_metadata(item.value)
                        description = str(meta.get("description", ""))
                        read_only = bool(meta.get("read_only", read_only))
                        stored_scope = str(meta.get("scope", ""))
                        if stored_scope:
                            try:
                                scope = MemoryScope(stored_scope)
                            except ValueError:
                                pass
                        else:
                            scope = candidate_scope
                        break
                except Exception:
                    continue
        result.append({
            "filename": f,
            "description": description,
            "scope": scope.value,
            "readOnly": read_only,
        })
    return result


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
