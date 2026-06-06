"""Agent ORM model for storing agent metadata."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Agent(Base):
    """Agent record — stores name, type, status, configuration, and hierarchy."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="代理名称")
    type: Mapped[str] = mapped_column(String(16), default="sub", comment="代理类型: main 或 sub")
    status: Mapped[str] = mapped_column(String(16), default="inactive", comment="代理状态: active, inactive, error")
    description: Mapped[str] = mapped_column(Text, default="", comment="代理描述")
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True, comment="父代理ID (NULL表示主代理)")
    tools: Mapped[list] = mapped_column(JSON, default=list, comment="工具名称列表")
    skills: Mapped[list] = mapped_column(JSON, default=list, comment="技能名称列表")
    prompts: Mapped[list] = mapped_column(JSON, default=list, comment="提示词/Cron Job 列表")
    files: Mapped[list] = mapped_column(JSON, default=list, comment="文件名称列表")
    undeletable: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否不可删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")
