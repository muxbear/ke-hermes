"""Agent management API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from agent.memory.scopes import MemoryScope
from api.agents.schemas import (
    AgentAddSkillRequest,
    AgentConfigRequest,
    AgentConfigUpdateRequest,
    AgentCreateRequest,
    AgentFileContent,
    AgentFileUpdateRequest,
    AgentInfo,
    AgentListResponse,
    AgentUpdateRequest,
    CronJobBrief,
    SkillBrief,
)
from api.agents.service import (
    add_agent_config,
    add_skill_to_agent,
    clone_agent,
    create_agent,
    delete_agent,
    get_agent,
    get_agent_cron_jobs,
    get_agent_file,
    get_agent_skills,
    list_agent_file_descriptions,
    list_agents,
    remove_agent_config,
    remove_skill_from_agent,
    save_agent_file,
    toggle_agent_status,
    update_agent,
    update_agent_config,
)
from api.deps import get_db
from core.decorators import handle_errors
from core.response import ApiResponse, ok

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=ApiResponse[AgentListResponse])
@handle_errors
async def agent_list(db: AsyncSession = Depends(get_db)):
    """获取当前用户的所有代理。"""  # noqa: D415
    result = await list_agents(db)
    return ok(result)


@router.get("/{agent_id}", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_get(agent_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个代理详情。"""  # noqa: D415
    result = await get_agent(db, agent_id)
    return ok(result)


@router.post("", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_create(req: AgentCreateRequest, db: AsyncSession = Depends(get_db)):
    """创建新代理（主代理或子代理）。"""  # noqa: D415
    result = await create_agent(db, req)
    return ok(result)


@router.delete("/{agent_id}", response_model=ApiResponse[None])
@handle_errors
async def agent_delete(agent_id: str, db: AsyncSession = Depends(get_db)):
    """删除代理，主代理会级联删除其所有子代理。"""  # noqa: D415
    await delete_agent(db, agent_id)
    return ok(None, "Agent deleted successfully")


@router.patch("/{agent_id}/status", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_toggle_status(agent_id: str, db: AsyncSession = Depends(get_db)):
    """切换代理的运行状态。"""  # noqa: D415
    result = await toggle_agent_status(db, agent_id)
    return ok(result)


@router.post("/{agent_id}/clone", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_clone(agent_id: str, db: AsyncSession = Depends(get_db)):
    """克隆代理，复制所有配置，状态置为 inactive。"""  # noqa: D415
    result = await clone_agent(db, agent_id)
    return ok(result)


@router.put("/{agent_id}", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_update(
    agent_id: str, req: AgentUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """更新代理的名称、描述和模型配置。"""  # noqa: D415
    result = await update_agent(db, agent_id, req)
    return ok(result)


@router.post("/{agent_id}/config", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_add_config(
    agent_id: str, req: AgentConfigRequest, db: AsyncSession = Depends(get_db)
):
    """为代理添加配置项（工具、技能、提示词、文件、子代理）。"""  # noqa: D415
    result = await add_agent_config(db, agent_id, req)
    return ok(result)


@router.delete("/{agent_id}/config", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_remove_config(
    agent_id: str, req: AgentConfigRequest, db: AsyncSession = Depends(get_db)
):
    """移除代理的配置项。对于子代理类型，会删除子代理。"""  # noqa: D415
    result = await remove_agent_config(db, agent_id, req)
    return ok(result)


@router.put("/{agent_id}/config", response_model=ApiResponse[AgentInfo])
@handle_errors
async def agent_update_config(
    agent_id: str, req: AgentConfigUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """更新代理的配置项（重命名文件 / 修改描述）。"""  # noqa: D415
    result = await update_agent_config(db, agent_id, req)
    return ok(result)


@router.get("/{agent_id}/file-descriptions")
@handle_errors
async def agent_file_descriptions(agent_id: str, db: AsyncSession = Depends(get_db)):
    """获取代理所有文件的描述列表。"""
    result = await list_agent_file_descriptions(db, agent_id)
    return ok(result)


@router.get(
    "/{agent_id}/files/{filename:path}",
    response_model=ApiResponse[AgentFileContent],
)
@handle_errors
async def agent_get_file(
    agent_id: str,
    filename: str,
    scope: MemoryScope | None = Query(None, description="记忆作用域"),
    db: AsyncSession = Depends(get_db),
):
    """获取代理文件内容。"""  # noqa: D415
    result = await get_agent_file(db, agent_id, filename, scope)
    return ok(result)


@router.put(
    "/{agent_id}/files/{filename:path}",
    response_model=ApiResponse[AgentFileContent],
)
@handle_errors
async def agent_save_file(
    agent_id: str,
    filename: str,
    req: AgentFileUpdateRequest,
    scope: MemoryScope | None = Query(None, description="记忆作用域"),
    db: AsyncSession = Depends(get_db),
):
    """保存代理文件内容。"""  # noqa: D415
    result = await save_agent_file(db, agent_id, filename, req.content, scope)
    return ok(result)


@router.get("/{agent_id}/skills", response_model=ApiResponse[list[SkillBrief]])
@handle_errors
async def agent_skills_list(agent_id: str, db: AsyncSession = Depends(get_db)):
    """获取智能体的所有已关联技能。"""  # noqa: D415
    result = await get_agent_skills(db, agent_id)
    return ok(result)


@router.post("/{agent_id}/skills", response_model=ApiResponse[list[SkillBrief]])
@handle_errors
async def agent_add_skill(
    agent_id: str, req: AgentAddSkillRequest, db: AsyncSession = Depends(get_db)
):
    """为智能体添加一个技能关联。"""  # noqa: D415
    result = await add_skill_to_agent(db, agent_id, req)
    return ok(result)


@router.delete("/{agent_id}/skills/{skill_id}", response_model=ApiResponse[None])
@handle_errors
async def agent_remove_skill(
    agent_id: str, skill_id: str, db: AsyncSession = Depends(get_db)
):
    """移除智能体的一个技能关联。"""  # noqa: D415
    await remove_skill_from_agent(db, agent_id, skill_id)
    return ok(None, "Skill removed from agent")


@router.get("/{agent_id}/cron-jobs", response_model=ApiResponse[list[CronJobBrief]])
@handle_errors
async def agent_cron_jobs(agent_id: str, db: AsyncSession = Depends(get_db)):
    """获取智能体的所有定时任务。"""  # noqa: D415
    result = await get_agent_cron_jobs(db, agent_id)
    return ok(result)
