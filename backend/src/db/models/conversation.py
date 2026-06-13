from datetime import datetime
from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func

import uuid

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # UUID
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    thread_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
