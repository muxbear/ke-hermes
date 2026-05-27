"""Business logic for MCP marketplace operations."""

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
    """Convert an ORM McpTool instance to a McpToolResponse with computed fields."""
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
    """List all MCP tools with optional filters, per-user install state, and install counts."""
    # Subquery: install counts per tool
    install_count_subq = (
        select(
            McpInstallation.mcp_tool_id,
            func.count(McpInstallation.id).label("install_count"),
        )
        .group_by(McpInstallation.mcp_tool_id)
        .subquery()
    )

    # Subquery: tool IDs installed by the current user
    installed_subq = (
        select(McpInstallation.mcp_tool_id)
        .where(McpInstallation.user_id == user_id)
        .subquery()
    )

    # Main query with computed columns
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

    # Apply category filter
    if category:
        stmt = stmt.where(McpTool.category == category)

    # Apply search filter (name, description, tags)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            McpTool.name.like(pattern)
            | McpTool.description.like(pattern)
            | func.cast(McpTool.tags, SQLiteJSON).like(pattern)
        )

    # Apply sort
    if sort == "rating":
        stmt = stmt.order_by(McpTool.rating.desc())
    elif sort == "recent":
        stmt = stmt.order_by(McpTool.created_at.desc())
    else:  # "popular"
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
    """Get a single MCP tool by ID with install count and user install state."""
    # Install count
    install_count = (
        await db.execute(
            select(func.count())
            .select_from(McpInstallation)
            .where(McpInstallation.mcp_tool_id == tool_id)
        )
    ).scalar() or 0

    # User install state
    user_installed = (
        await db.execute(
            select(McpInstallation.id).where(
                McpInstallation.user_id == user_id,
                McpInstallation.mcp_tool_id == tool_id,
            )
        )
    ).scalar_one_or_none() is not None

    # Tool record
    tool = (
        await db.execute(select(McpTool).where(McpTool.id == tool_id))
    ).scalar_one_or_none()
    if tool is None:
        raise HTTPException(status_code=404, detail="MCP tool not found")

    return _tool_to_response(tool, installs=install_count, installed=user_installed)


async def install_mcp_tool(
    db: AsyncSession,
    user_id: str,
    mcp_id: str,
    config: dict | None = None,
) -> None:
    """Install an MCP tool for the current user."""
    # Verify tool exists
    tool = (
        await db.execute(select(McpTool).where(McpTool.id == mcp_id))
    ).scalar_one_or_none()
    if tool is None:
        raise HTTPException(status_code=404, detail="MCP tool not found")

    # Check for duplicate installation
    existing = (
        await db.execute(
            select(McpInstallation).where(
                McpInstallation.user_id == user_id,
                McpInstallation.mcp_tool_id == mcp_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tool already installed")

    # Create installation record
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
    """Uninstall an MCP tool for the current user."""
    installation = (
        await db.execute(
            select(McpInstallation).where(
                McpInstallation.user_id == user_id,
                McpInstallation.mcp_tool_id == tool_id,
            )
        )
    ).scalar_one_or_none()
    if installation is None:
        raise HTTPException(status_code=404, detail="Tool not installed")
    await db.delete(installation)


async def seed_mcp_tools(db: AsyncSession) -> None:
    """Seed mcp_tools from JSON file if the table is empty. Idempotent."""
    count = (await db.execute(select(func.count()).select_from(McpTool))).scalar() or 0
    if count > 0:
        logger.info("MCP tools table has %d rows, skipping seed", count)
        return

    if not os.path.isfile(_SEED_PATH):
        logger.warning("MCP seed file not found: %s", _SEED_PATH)
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
    logger.info("Seeded %d MCP tools", len(tools_data))
