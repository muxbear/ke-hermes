"""AIModel ORM model for storing AI model metadata."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AIModel(Base):
    """AI model record — belongs to a provider, stores type, status, parameters, and usage stats."""

    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="所属提供商ID")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="模型名称（机器名，如 gpt-4o）")
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="展示名称（如 GPT-4o）")
    type: Mapped[str] = mapped_column(String(16), nullable=False, comment="模型类型: llm, vision, audio, video, embedding, image-gen, speech")
    status: Mapped[str] = mapped_column(String(16), default="active", comment="模型状态: active, beta, deprecated")
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="上下文窗口大小（tokens）")
    call_count: Mapped[int] = mapped_column(Integer, default=0, comment="调用次数")
    description: Mapped[str] = mapped_column(Text, default="", comment="描述")
    release_date: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="发布日期（如 2024-05）")
    params: Mapped[list] = mapped_column(JSON, default=list, comment="默认参数列表")
    used_by_agents: Mapped[list] = mapped_column(JSON, default=list, comment="使用此模型的代理名称列表")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="所属用户ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")
