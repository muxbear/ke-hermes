"""McpTool ORM model for the MCP marketplace catalog."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class McpTool(Base):
    """MCP tool catalog entry — stores metadata, config schema, and classification."""

    __tablename__ = "mcp_tools"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True, comment="工具名称"
    )
    description: Mapped[str] = mapped_column(Text, default="", comment="工具描述")
    icon: Mapped[str] = mapped_column(String(16), default="🔧", comment="Emoji 图标")
    author: Mapped[str] = mapped_column(String(128), default="", comment="作者名称")
    version: Mapped[str] = mapped_column(String(32), default="1.0.0", comment="版本号")
    license: Mapped[str] = mapped_column(String(128), default="MIT", comment="许可证")
    repository: Mapped[str] = mapped_column(
        String(512), default="", comment="源码仓库 URL"
    )
    rating: Mapped[float] = mapped_column(Float, default=0.0, comment="评分 0-5")
    category: Mapped[str] = mapped_column(
        String(32), default="custom", index=True, comment="分类 key"
    )
    tags: Mapped[list] = mapped_column(JSON, default=list, comment="标签数组")
    features: Mapped[list] = mapped_column(JSON, default=list, comment="功能描述数组")
    official: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="官方认证标记"
    )
    config_schema: Mapped[list] = mapped_column(
        JSON, default=list, comment="配置字段定义数组"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
