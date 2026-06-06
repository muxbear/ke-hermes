"""Tool management API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.tools.schemas import (
    ToolCreateRequest,
    ToolInfo,
    ToolListResponse,
    ToolToggleRequest,
    ToolUpdateRequest,
)
from api.tools.service import (
    create_tool,
    delete_tool,
    get_tool,
    get_tools_by_agent,
    list_tools,
    toggle_tool_enabled,
    update_tool,
)
from core.response import ApiResponse, error, ok

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/list", response_model=ApiResponse[ToolListResponse])
async def tool_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    source: str | None = Query(None, description="来源筛选: builtin/third_party"),
    category: str | None = Query(None, description="分类筛选"),
    status: str | None = Query(None, description="状态筛选: enabled/disabled/unavailable"),
    keyword: str | None = Query(None, description="搜索关键词（匹配名称、标签）"),
    db: AsyncSession = Depends(get_db),
):
    """分页列出所有工具，支持来源、分类、状态筛选和关键词搜索。"""  # noqa: D415
    try:
        result = await list_tools(db, page, page_size, source, category, status, keyword)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.get("/by-agent/{agent_id}", response_model=ApiResponse[list[ToolInfo]])
async def tools_by_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取指定智能体已关联的工具列表。"""  # noqa: D415
    try:
        result = await get_tools_by_agent(db, agent_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.post("", response_model=ApiResponse[ToolInfo])
async def tool_create(
    req: ToolCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建第三方工具。"""  # noqa: D415
    try:
        result = await create_tool(db, req)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.get("/{tool_id}", response_model=ApiResponse[ToolInfo])
async def tool_get(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个工具详情。"""  # noqa: D415
    try:
        result = await get_tool(db, tool_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.put("/{tool_id}", response_model=ApiResponse[ToolInfo])
async def tool_update(
    tool_id: str,
    req: ToolUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新工具元数据，只更新传入的非空字段。"""  # noqa: D415
    try:
        result = await update_tool(db, tool_id, req)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.patch("/{tool_id}/toggle", response_model=ApiResponse[ToolInfo])
async def tool_toggle(
    tool_id: str,
    req: ToolToggleRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """切换工具的启用/禁用状态。"""  # noqa: D415
    try:
        result = await toggle_tool_enabled(db, tool_id, req.enabled)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.delete("/{tool_id}", response_model=ApiResponse[dict])
async def tool_delete(
    tool_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除工具（仅第三方工具可删除）。"""  # noqa: D415
    try:
        result = await delete_tool(db, tool_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


