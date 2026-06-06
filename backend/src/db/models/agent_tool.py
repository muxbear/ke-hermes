"""Agent-Tool junction table for many-to-many relationship."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.agent import Agent
    from db.models.tool import Tool


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AgentTool(Base):
    """Junction table linking agents to tools."""

    __tablename__ = "agent_tools"

    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True
    )
    tool_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # Relationships
    agent: Mapped[Agent] = relationship("Agent", back_populates="tool_links")
    tool: Mapped[Tool] = relationship("Tool")
