"""Agent ORM model for storing agent metadata."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.agent_tool import AgentTool


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Agent(Base):
    """Agent record — stores name, type, status, configuration, and hierarchy."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="代理名称")
    type: Mapped[str] = mapped_column(String(16), default="sub", comment="代理类型: main 或 sub")
    status: Mapped[str] = mapped_column(String(16), default="inactive", comment="代理状态: active, inactive, error")
    description: Mapped[str] = mapped_column(Text, default="", comment="代理描述")
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True, comment="父代理ID (NULL表示主代理)")
    system_prompt: Mapped[str] = mapped_column(Text, default="", comment="系统提示词")
    files: Mapped[list] = mapped_column(JSON, default=list, comment="文件名称列表")
    provider_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="关联的模型提供商ID")
    model_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="关联的AI模型ID")
    undeletable: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否不可删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")

    # Relationships
    tool_links: Mapped[list[AgentTool]] = relationship(
        "AgentTool", back_populates="agent", cascade="all, delete-orphan"
    )
