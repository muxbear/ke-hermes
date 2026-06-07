"""Tool CRUD business logic and seed data."""
import logging

from fastapi import HTTPException
from sqlalchemy import Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.tools.schemas import (
    ToolCreateRequest,
    ToolInfo,
    ToolListResponse,
    ToolUpdateRequest,
)
from db.models.agent_tool import AgentTool
from db.models.tool import Tool

logger = logging.getLogger(__name__)

# ── Category aliases for data compatibility ──────────────────────────────
CATEGORY_ALIASES: dict[str, str] = {
    "code": "code",
    "network": "network",
    "message": "message",
    "file": "file",
    "data": "data",
    "ai": "ai",
    "system": "system",
    "other": "other",
}


def _tool_to_info(tool: Tool, agent_ids: list[str] | None = None) -> ToolInfo:
    """Convert ORM Tool + optional agent IDs to a ToolInfo response."""
    return ToolInfo(
        id=tool.id,
        name=tool.name,
        display_name=tool.display_name,
        description=tool.description or "",
        category=tool.category,
        source=tool.source,
        status=tool.status,
        version=tool.version,
        author=tool.author or "",
        used_by_agents=agent_ids or [],
        tags=tool.tags or [],
        params=tool.params or [],
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


async def _get_agent_ids_for_tool(db: AsyncSession, tool_id: str) -> list[str]:
    """Get the list of agent IDs that use this tool."""
    stmt = select(AgentTool.agent_id).where(AgentTool.tool_id == tool_id)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


async def list_tools(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    source: str | None = None,
    category: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> ToolListResponse:
    """List tools with pagination and optional filters."""
    offset = max(0, (page - 1) * page_size)
    page_size = max(1, min(page_size, 100))

    conditions = []
    if source:
        conditions.append(Tool.source == source)
    if category:
        conditions.append(Tool.category == category)
    if status:
        conditions.append(Tool.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(
            (Tool.display_name.ilike(pattern))
            | (Tool.name.ilike(pattern))
            | (Tool.description.ilike(pattern))
            | (Tool.tags.cast(Text).ilike(pattern))
        )

    total_stmt = select(func.count()).select_from(Tool)
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = select(Tool).order_by(Tool.created_at.desc()).offset(offset).limit(page_size)
    if conditions:
        stmt = stmt.where(*conditions)
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for row in rows:
        agent_ids = await _get_agent_ids_for_tool(db, row.id)
        items.append(_tool_to_info(row, agent_ids))

    return ToolListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_tool(db: AsyncSession, tool_id: str) -> ToolInfo:
    """Get a single tool by ID."""
    stmt = select(Tool).where(Tool.id == tool_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="工具不存在")
    agent_ids = await _get_agent_ids_for_tool(db, tool_id)
    return _tool_to_info(row, agent_ids)


async def create_tool(db: AsyncSession, req: ToolCreateRequest) -> ToolInfo:
    """Create a third-party tool."""
    existing = (await db.execute(select(Tool).where(Tool.name == req.name))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"工具标识 '{req.name}' 已存在")

    tool = Tool(
        name=req.name,
        display_name=req.display_name,
        description=req.description or "",
        category=req.category,
        source="third_party",
        status=req.status,
        version=req.version,
        author="自定义",
        tags=req.tags or [],
        params=[p.model_dump() for p in req.params],
    )
    db.add(tool)
    await db.flush()
    logger.info("Created third-party tool '%s' (id=%s)", req.name, tool.id)
    return _tool_to_info(tool)


async def update_tool(
    db: AsyncSession, tool_id: str, req: ToolUpdateRequest
) -> ToolInfo:
    """Update tool metadata. Only non-None fields are updated. Builtin tools cannot be modified."""
    stmt = select(Tool).where(Tool.id == tool_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="工具不存在")
    if row.source == "builtin":
        raise HTTPException(status_code=403, detail="内置工具不可修改")

    update_data = req.model_dump(exclude_none=True)

    # Check for duplicate name when changing the name field
    if "name" in update_data and update_data["name"] != row.name:
        existing = (await db.execute(
            select(Tool).where(Tool.name == update_data["name"])
        )).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=409, detail=f"工具标识 '{update_data['name']}' 已存在")

    for key, value in update_data.items():
        if key == "params" and value is not None:
            value = [p if isinstance(p, dict) else p.model_dump() for p in value]
        setattr(row, key, value)

    await db.flush()
    agent_ids = await _get_agent_ids_for_tool(db, tool_id)
    return _tool_to_info(row, agent_ids)


async def delete_tool(db: AsyncSession, tool_id: str) -> dict:
    """Delete a tool. Only third-party tools can be deleted. Cleans up agent-tool links first."""
    stmt = select(Tool).where(Tool.id == tool_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="工具不存在")
    if row.source == "builtin":
        raise HTTPException(status_code=403, detail="内置工具不可删除")

    # Explicitly delete agent-tool links first (belt-and-suspenders with FK CASCADE)
    link_stmt = select(AgentTool).where(AgentTool.tool_id == tool_id)
    links = (await db.execute(link_stmt)).scalars().all()
    for link in links:
        await db.delete(link)

    await db.delete(row)
    await db.flush()
    logger.info("Deleted tool '%s' (id=%s) with %d agent links", row.name, tool_id, len(links))
    return {"deleted": True, "id": tool_id}


async def toggle_tool_enabled(
    db: AsyncSession, tool_id: str, enabled: bool
) -> ToolInfo:
    """Toggle a tool's enabled/disabled status."""
    stmt = select(Tool).where(Tool.id == tool_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="工具不存在")

    row.status = "enabled" if enabled else "disabled"
    await db.flush()
    agent_ids = await _get_agent_ids_for_tool(db, tool_id)
    return _tool_to_info(row, agent_ids)


async def get_tools_by_agent(
    db: AsyncSession, agent_id: str
) -> list[ToolInfo]:
    """Get all tools linked to a specific agent."""
    stmt = (
        select(Tool)
        .join(AgentTool, AgentTool.tool_id == Tool.id)
        .where(AgentTool.agent_id == agent_id)
        .order_by(Tool.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = []
    for row in rows:
        agent_ids = await _get_agent_ids_for_tool(db, row.id)
        items.append(_tool_to_info(row, agent_ids))
    return items


# ── Builtin tool seed data ────────────────────────────────────────────────

BUILTIN_TOOLS: list[dict] = [
    {
        "name": "execute_code",
        "display_name": "代码执行",
        "description": "在沙箱环境中执行 Python / JavaScript 代码，返回标准输出与错误信息。",
        "category": "code",
        "version": "1.3.0",
        "tags": ["python", "js", "sandbox"],
        "params": [
            {"key": "language", "label": "编程语言", "required": True, "type": "string"},
            {"key": "timeout", "label": "超时(s)", "required": False, "type": "number"},
        ],
    },
    {
        "name": "shell_command",
        "display_name": "Shell 命令",
        "description": "在受限 Shell 环境中执行系统命令，支持管道和重定向。",
        "category": "code",
        "version": "1.1.0",
        "tags": ["shell", "bash", "cli"],
        "params": [
            {"key": "command", "label": "命令", "required": True, "type": "string"},
            {"key": "cwd", "label": "工作目录", "required": False, "type": "string"},
        ],
    },
    {
        "name": "http_request",
        "display_name": "HTTP 请求",
        "description": "发送 HTTP/HTTPS 请求，支持 GET / POST / PUT / DELETE / PATCH，自定义 Header 与 Body，自动跟随重定向，内置 SSRF 防护。",
        "category": "network",
        "version": "2.1.0",
        "tags": ["http", "api", "rest"],
        "params": [
            {"key": "url", "label": "目标 URL", "required": True, "type": "string"},
            {"key": "method", "label": "HTTP 方法", "required": False, "type": "string"},
            {"key": "headers", "label": "请求头", "required": False, "type": "object"},
            {"key": "body", "label": "请求体", "required": False, "type": "string"},
            {"key": "timeout", "label": "超时(秒)", "required": False, "type": "number"},
        ],
    },
    {
        "name": "tavily_search",
        "display_name": "Tavily 网络搜索",
        "description": "通过 Tavily Search API 对互联网进行实时检索，支持深度搜索、时间过滤、AI 摘要，返回结构化搜索结果与来源 URL。",
        "category": "network",
        "version": "2.0.0",
        "tags": ["search", "tavily", "web", "ai"],
        "params": [
            {
                "key": "query",
                "label": "搜索关键词",
                "required": True,
                "type": "string",
                "description": "搜索关键词或问题，支持中英文。越具体越容易获得精确结果。",
            },
            {
                "key": "search_depth",
                "label": "搜索深度",
                "required": False,
                "type": "string",
                "enum": ["basic", "advanced"],
                "default": "basic",
                "description": "basic 快速搜索（约1-2秒），advanced 深度搜索（约5-10秒，结果更全面）。默认 basic。",
            },
            {
                "key": "topic",
                "label": "搜索主题",
                "required": False,
                "type": "string",
                "enum": ["general", "news", "finance"],
                "default": "general",
                "description": "general 通用搜索，news 新闻搜索（偏重新闻资讯），finance 金融搜索（偏重财经数据）。默认 general。",
            },
            {
                "key": "time_range",
                "label": "时间范围",
                "required": False,
                "type": "string",
                "enum": ["day", "week", "month", "year"],
                "description": "限制搜索结果的时间范围：day 一天内，week 一周内，month 一月内，year 一年内。不填则不限制时间。",
            },
            {
                "key": "max_results",
                "label": "最大结果数",
                "required": False,
                "type": "number",
                "default": 10,
                "description": "返回的最大搜索结果数，范围 1-20。默认 10。",
            },
            {
                "key": "include_answer",
                "label": "返回 AI 摘要",
                "required": False,
                "type": "boolean",
                "default": True,
                "description": "是否让 Tavily 根据搜索结果生成一段 AI 摘要回答。默认开启，建议保持开启以获取更好的信息概览。",
            },
            {
                "key": "include_raw_content",
                "label": "包含原始内容",
                "required": False,
                "type": "boolean",
                "default": False,
                "description": "是否在每条结果中包含抓取到的原始网页 Markdown 内容。默认关闭，仅在需要完整原文时开启。",
            },
        ],
    },
    {
        "name": "web_scraper",
        "display_name": "网页抓取",
        "description": "抓取指定 URL 的页面内容，支持提取正文、链接与结构化数据。",
        "category": "network",
        "version": "1.2.0",
        "tags": ["scrape", "html", "extract"],
        "params": [
            {"key": "url", "label": "目标 URL", "required": True, "type": "string"},
            {"key": "selector", "label": "CSS 选择器", "required": False, "type": "string"},
        ],
    },
    {
        "name": "read_file",
        "display_name": "文件读取",
        "description": "读取本地或远程文件内容，支持文本、JSON、CSV、PDF 等格式。",
        "category": "file",
        "version": "1.0.4",
        "tags": ["file", "read", "pdf"],
        "params": [
            {"key": "path", "label": "文件路径", "required": True, "type": "string"},
            {"key": "encoding", "label": "编码", "required": False, "type": "string"},
        ],
    },
    {
        "name": "write_file",
        "display_name": "文件写入",
        "description": "将内容写入文件，支持覆盖、追加模式，自动创建父目录。",
        "category": "file",
        "version": "1.0.4",
        "tags": ["file", "write"],
        "params": [
            {"key": "path", "label": "文件路径", "required": True, "type": "string"},
            {"key": "content", "label": "内容", "required": True, "type": "string"},
            {"key": "mode", "label": "模式", "required": False, "type": "string"},
        ],
    },
    {
        "name": "sql_query",
        "display_name": "SQL 查询",
        "description": "连接数据库执行 SQL 语句，支持 MySQL、PostgreSQL、SQLite。",
        "category": "data",
        "version": "1.1.0",
        "tags": ["sql", "database", "query"],
        "params": [
            {"key": "dsn", "label": "连接串", "required": True, "type": "string"},
            {"key": "query", "label": "SQL", "required": True, "type": "string"},
        ],
    },
    {
        "name": "get_datetime",
        "display_name": "当前时间",
        "description": "获取当前日期时间，支持指定时区与格式化输出。",
        "category": "system",
        "version": "1.0.0",
        "tags": ["time", "date", "timezone"],
        "params": [
            {"key": "timezone", "label": "时区", "required": False, "type": "string"},
            {"key": "format", "label": "格式串", "required": False, "type": "string"},
        ],
    },
    {
        "name": "image_generate",
        "display_name": "图像生成",
        "description": "根据文本提示生成图像，支持 DALL-E、Stable Diffusion 后端切换。",
        "category": "ai",
        "version": "2.0.0",
        "tags": ["image", "ai", "dalle"],
        "params": [
            {"key": "prompt", "label": "提示词", "required": True, "type": "string"},
            {"key": "size", "label": "尺寸", "required": False, "type": "string"},
        ],
    },
    {
        "name": "text_embedding",
        "display_name": "文本向量化",
        "description": "将文本转化为高维向量，用于语义搜索与相似度计算。",
        "category": "ai",
        "version": "1.2.0",
        "tags": ["embedding", "vector", "nlp"],
        "params": [
            {"key": "text", "label": "文本", "required": True, "type": "string"},
            {"key": "model", "label": "模型 ID", "required": False, "type": "string"},
        ],
    },
]

async def seed_builtin_tools(db: AsyncSession) -> None:
    """Seed builtin tools if the tools table is empty. Idempotent."""
    count = (await db.execute(select(func.count()).select_from(Tool))).scalar() or 0
    if count > 0:
        logger.info("Tools table has %d rows, skipping seed", count)
        return

    for t in BUILTIN_TOOLS:
        tool = Tool(
            name=t["name"],
            display_name=t["display_name"],
            description=t["description"],
            category=t["category"],
            source="builtin",
            status="enabled",
            version=t["version"],
            author="ke-hermes",
            tags=t.get("tags", []),
            params=t.get("params", []),
        )
        db.add(tool)

    logger.info("Seeded %d builtin tools", len(BUILTIN_TOOLS))
