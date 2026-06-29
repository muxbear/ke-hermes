"""Department / organization node ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Department(Base):
    """Organization department node with hierarchical parent-child structure."""

    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="部门名称")
    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="部门编码,如 KH,RD,RD-FE"
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="父部门ID",
    )
    type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="dept", comment="类型: group/center/dept/team"
    )
    level: Mapped[int] = mapped_column(
        Integer, default=0, comment="层级: 0=根 1=一级 2=二级..."
    )
    manager_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("personnel.id", ondelete="SET NULL"),
        nullable=True,
        comment="负责人ID->personnel",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    address: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="地址")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="部门电话")
    email: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="部门邮箱")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[str] = mapped_column(
        String(16), default="active", comment="状态: active/inactive"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
