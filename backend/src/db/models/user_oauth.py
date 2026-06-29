import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class UserOAuth(Base):
    __tablename__ = "user_oauths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    open_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("provider", "open_id", name="uq_oauth_provider_openid"),
    )
