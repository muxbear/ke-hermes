"""MCP marketplace API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.mcp.schemas import InstallMcpRequest, McpToolResponse
from api.mcp.service import (
    get_mcp_tool,
    install_mcp_tool,
    list_mcp_tools,
    uninstall_mcp_tool,
)
from core.decorators import handle_errors
from core.response import ApiResponse, ok

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/tools", response_model=ApiResponse[list[McpToolResponse]])
@handle_errors
async def mcp_tool_list(
    category: str | None = Query(None, description="Category filter key"),
    search: str | None = Query(None, description="Search keyword"),
    sort: str | None = Query("popular", description="Sort: popular, rating, recent"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[McpToolResponse]]:
    """List all MCP tools with optional filters and per-user install state."""
    result = await list_mcp_tools(db, user_id, category, search, sort)
    return ok(result)


@router.get("/tools/{tool_id}", response_model=ApiResponse[McpToolResponse])
@handle_errors
async def mcp_tool_detail(
    tool_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[McpToolResponse]:
    """Get a single MCP tool detail."""
    result = await get_mcp_tool(db, tool_id, user_id)
    return ok(result)


@router.post("/tools/{mcp_id}/install", response_model=ApiResponse[None])
@handle_errors
async def mcp_tool_install(
    mcp_id: str,
    body: InstallMcpRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """Install an MCP tool for the current user."""
    await install_mcp_tool(db, user_id, mcp_id, body.config)
    return ok(message="installed")


@router.delete("/tools/{tool_id}/uninstall", response_model=ApiResponse[None])
@handle_errors
async def mcp_tool_uninstall(
    tool_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """Uninstall an MCP tool for the current user."""
    await uninstall_mcp_tool(db, user_id, tool_id)
    return ok(message="uninstalled")
