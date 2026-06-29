"""Personnel / system user ORM model."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Personnel(Base):
    """Organization personnel record, optionally linked to an auth user account."""

    __tablename__ = "personnel"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        comment="关联的认证账号ID,为空表示无登录权限",
    )
    dept_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门ID",
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    employee_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="工号"
    )
    position: Mapped[str] = mapped_column(String(128), default="", comment="职位")
    email: Mapped[str] = mapped_column(String(128), default="", comment="工作邮箱")
    phone: Mapped[str] = mapped_column(String(20), default="", comment="手机号")
    status: Mapped[str] = mapped_column(
        String(16), default="active", comment="状态: active/inactive/pending"
    )
    join_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="入职日期")
    avatar: Mapped[str] = mapped_column(String(256), default="", comment="头像URL")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="部门内排序")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
