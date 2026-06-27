"""MCP 广场业务逻辑：工具列表、安装、卸载与种子数据。"""

import json
import logging
import os
import uuid

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.asyncio import AsyncSession

from api.mcp.schemas import McpToolResponse
from db.models.mcp_installation import McpInstallation
from db.models.mcp_tool import McpTool

logger = logging.getLogger(__name__)

_SEED_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "db",
        "seeds",
        "mcp_tools_seed.json",
    )
)


def _tool_to_response(
    tool: McpTool,
    installs: int = 0,
    installed: bool = False,
) -> McpToolResponse:
    """将 ORM McpTool 实例转换为包含计算字段的 McpToolResponse。"""
    return McpToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        icon=tool.icon,
        author=tool.author,
        version=tool.version,
        license=tool.license,
        repository=tool.repository,
        installs=installs,
        rating=tool.rating,
        category=tool.category,
        tags=tool.tags or [],
        features=tool.features or [],
        official=tool.official,
        installed=installed,
        config_schema=tool.config_schema or [],
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


async def list_mcp_tools(
    db: AsyncSession,
    user_id: str,
    category: str | None = None,
    search: str | None = None,
    sort: str | None = "popular",
) -> list[McpToolResponse]:
    """列出所有 MCP 工具，支持可选筛选、当前用户安装状态和安装数量。"""
    # 子查询：每个工具的安装数量
    install_count_subq = (
        select(
            McpInstallation.mcp_tool_id,
            func.count(McpInstallation.id).label("install_count"),
        )
        .group_by(McpInstallation.mcp_tool_id)
        .subquery()
    )

    # 子查询：当前用户已安装的工具 ID
    installed_subq = (
        select(McpInstallation.mcp_tool_id)
        .where(McpInstallation.user_id == user_id)
        .subquery()
    )

    # 主查询，带计算列
    stmt = select(
        McpTool,
        func.coalesce(install_count_subq.c.install_count, 0).label("installs"),
        case(
            (McpTool.id.in_(select(installed_subq.c.mcp_tool_id)), True),
            else_=False,
        ).label("installed"),
    ).outerjoin(
        install_count_subq,
        McpTool.id == install_count_subq.c.mcp_tool_id,
    )

    # 按分类筛选
    if category:
        stmt = stmt.where(McpTool.category == category)

    # 按关键字搜索（名称、描述、标签）
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            McpTool.name.like(pattern)
            | McpTool.description.like(pattern)
            | func.cast(McpTool.tags, SQLiteJSON).like(pattern)
        )

    # 排序
    if sort == "rating":
        stmt = stmt.order_by(McpTool.rating.desc())
    elif sort == "recent":
        stmt = stmt.order_by(McpTool.created_at.desc())
    else:  # 默认按流行度排序
        stmt = stmt.order_by(
            func.coalesce(install_count_subq.c.install_count, 0).desc()
        )

    rows = (await db.execute(stmt)).all()
    return [
        _tool_to_response(row[0], installs=row.installs, installed=row.installed)
        for row in rows
    ]


async def get_mcp_tool(
    db: AsyncSession,
    tool_id: str,
    user_id: str,
) -> McpToolResponse:
    """根据 ID 获取单个 MCP 工具，含安装数量和当前用户安装状态。"""
    # 安装数量
    install_count = (
        await db.execute(
            select(func.count())
            .select_from(McpInstallation)
            .where(McpInstallation.mcp_tool_id == tool_id)
        )
    ).scalar() or 0

    # 当前用户是否已安装
    user_installed = (
        await db.execute(
            select(McpInstallation.id).where(
                McpInstallation.user_id == user_id,
                McpInstallation.mcp_tool_id == tool_id,
            )
        )
    ).scalar_one_or_none() is not None

    # 查询工具记录
    tool = (
        await db.execute(select(McpTool).where(McpTool.id == tool_id))
    ).scalar_one_or_none()
    if tool is None:
        raise HTTPException(status_code=404, detail="MCP 工具未找到")

    return _tool_to_response(tool, installs=install_count, installed=user_installed)


async def install_mcp_tool(
    db: AsyncSession,
    user_id: str,
    mcp_id: str,
    config: dict | None = None,
) -> None:
    """为当前用户安装 MCP 工具。"""
    # 校验工具是否存在
    tool = (
        await db.execute(select(McpTool).where(McpTool.id == mcp_id))
    ).scalar_one_or_none()
    if tool is None:
        raise HTTPException(status_code=404, detail="MCP 工具未找到")

    # 检查是否已安装
    existing = (
        await db.execute(
            select(McpInstallation).where(
                McpInstallation.user_id == user_id,
                McpInstallation.mcp_tool_id == mcp_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="工具已安装")

    # 创建安装记录
    db.add(
        McpInstallation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            mcp_tool_id=mcp_id,
            config=config or {},
        )
    )


async def uninstall_mcp_tool(
    db: AsyncSession,
    user_id: str,
    tool_id: str,
) -> None:
    """为当前用户卸载 MCP 工具。"""
    installation = (
        await db.execute(
            select(McpInstallation).where(
                McpInstallation.user_id == user_id,
                McpInstallation.mcp_tool_id == tool_id,
            )
        )
    ).scalar_one_or_none()
    if installation is None:
        raise HTTPException(status_code=404, detail="工具未安装")
    await db.delete(installation)


async def seed_mcp_tools(db: AsyncSession) -> None:
    """从 JSON 文件填充 mcp_tools 表，仅当表为空时执行，可重复调用。"""
    count = (await db.execute(select(func.count()).select_from(McpTool))).scalar() or 0
    if count > 0:
        logger.info("MCP 工具表已有 %d 条记录，跳过种子数据", count)
        return

    if not os.path.isfile(_SEED_PATH):
        logger.warning("MCP 种子文件未找到: %s", _SEED_PATH)
        return

    with open(_SEED_PATH, encoding="utf-8") as f:
        tools_data: list[dict] = json.load(f)

    for td in tools_data:
        db.add(
            McpTool(
                name=td["name"],
                description=td.get("description", ""),
                icon=td.get("icon", "🔧"),
                author=td.get("author", ""),
                version=td.get("version", "1.0.0"),
                license=td.get("license", "MIT"),
                repository=td.get("repository", ""),
                rating=td.get("rating", 0.0),
                category=td.get("category", "custom"),
                tags=td.get("tags", []),
                features=td.get("features", []),
                official=td.get("official", False),
                config_schema=td.get("config_schema", []),
            )
        )
    await db.flush()
    logger.info("已填充 %d 个 MCP 工具", len(tools_data))
