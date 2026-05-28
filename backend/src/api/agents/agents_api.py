"""Agent management API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.agents.schemas import (
    AgentConfigRequest,
    AgentCreateRequest,
    AgentInfo,
    AgentListResponse,
)
from api.agents.service import (
    add_agent_config,
    clone_agent,
    create_agent,
    delete_agent,
    get_agent,
    list_agents,
    remove_agent_config,
    toggle_agent_status,
)
from api.deps import get_current_user_id, get_db
from core.response import ApiResponse, error, ok

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=ApiResponse[AgentListResponse])
async def agent_list(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有代理。"""  # noqa: D415
    try:
        result = await list_agents(db, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.get("/{agent_id}", response_model=ApiResponse[AgentInfo])
async def agent_get(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取单个代理详情。"""  # noqa: D415
    try:
        result = await get_agent(db, agent_id, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.post("", response_model=ApiResponse[AgentInfo])
async def agent_create(
    req: AgentCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新代理（主代理或子代理）。"""  # noqa: D415
    try:
        result = await create_agent(db, req, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.delete("/{agent_id}", response_model=ApiResponse[None])
async def agent_delete(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除代理，主代理会级联删除其所有子代理。"""  # noqa: D415
    try:
        await delete_agent(db, agent_id, user_id)
        return ok(None, "Agent deleted successfully")
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.patch("/{agent_id}/status", response_model=ApiResponse[AgentInfo])
async def agent_toggle_status(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """切换代理的运行状态。"""  # noqa: D415
    try:
        result = await toggle_agent_status(db, agent_id, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.post("/{agent_id}/clone", response_model=ApiResponse[AgentInfo])
async def agent_clone(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """克隆代理，复制所有配置，状态置为 inactive。"""  # noqa: D415
    try:
        result = await clone_agent(db, agent_id, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.post("/{agent_id}/config", response_model=ApiResponse[AgentInfo])
async def agent_add_config(
    agent_id: str,
    req: AgentConfigRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """为代理添加配置项（工具、技能、提示词、文件、子代理）。"""  # noqa: D415
    try:
        result = await add_agent_config(db, agent_id, req, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.delete("/{agent_id}/config", response_model=ApiResponse[AgentInfo])
async def agent_remove_config(
    agent_id: str,
    req: AgentConfigRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """移除代理的配置项。对于子代理类型，会删除子代理。"""  # noqa: D415
    try:
        result = await remove_agent_config(db, agent_id, req, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise
