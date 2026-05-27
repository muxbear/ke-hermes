"""McpInstallation ORM model for per-user MCP tool installation records."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class McpInstallation(Base):
    """Per-user MCP tool installation — tracks which tools a user has installed and their config."""

    __tablename__ = "mcp_installations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="用户 ID"
    )
    mcp_tool_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="MCP 工具 ID"
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict, comment="用户配置值")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="安装时间"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "mcp_tool_id", name="uq_installation_user_tool"),
    )
