import uuid

from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class KnowledgeBaseEntity(Base):
    __tablename__ = "knowledge_base_entities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    kb_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    mentions: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata_", JSON, default=dict)
