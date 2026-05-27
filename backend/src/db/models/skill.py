"""Skill ORM model for storing uploaded skill records."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Skill(Base):
    """Uploaded skill record — tracks name, validation status, source, and metadata."""

    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(64), index=True, comment="技能名称")
    valid: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否校验成功")
    source: Mapped[str] = mapped_column(String(32), default="local", comment="技能来源: local, clawhub 等")
    description: Mapped[str] = mapped_column(Text, default="", comment="技能描述")
    license: Mapped[str] = mapped_column(String(128), default="", comment="许可证")
    icon: Mapped[str] = mapped_column(String(64), default="", comment="图标名称")
    category: Mapped[str] = mapped_column(String(32), default="custom", comment="技能分类")
    prompt: Mapped[str] = mapped_column(Text, default="", comment="系统提示词")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否内置")
    user_id: Mapped[str] = mapped_column(String(36), index=True, comment="上传用户ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="上传时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
