import uuid

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class KnowledgeBaseRelation(Base):
    __tablename__ = "knowledge_base_relations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    kb_id: Mapped[str] = mapped_column(String(36), nullable=False)
    doc_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    from_entity: Mapped[str] = mapped_column(String(256), nullable=False)
    to_entity: Mapped[str] = mapped_column(String(256), nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    source_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    target_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
