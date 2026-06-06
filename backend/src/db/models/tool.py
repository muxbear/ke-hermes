"""Tool ORM model for storing tool records (builtin and third-party)."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Tool(Base):
    """Tool record — tracks name, category, source, status, and parameter definitions."""

    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, comment="工具标识符，如 execute_code")
    display_name: Mapped[str] = mapped_column(String(128), comment="显示名称，如 代码执行")
    description: Mapped[str] = mapped_column(Text, default="", comment="工具描述")
    category: Mapped[str] = mapped_column(
        String(32), default="other", comment="功能分类: code/network/message/file/data/ai/system/other"
    )
    source: Mapped[str] = mapped_column(
        String(32), default="builtin", comment="来源: builtin/third_party"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="enabled", comment="状态: enabled/disabled/unavailable"
    )
    version: Mapped[str] = mapped_column(String(32), default="1.0.0", comment="版本号")
    author: Mapped[str] = mapped_column(String(128), default="", comment="作者")
    tags: Mapped[list] = mapped_column(JSON, default=list, comment="标签数组")
    params: Mapped[list] = mapped_column(JSON, default=list, comment="参数定义数组 [{key, label, required, type}]")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
