from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EventSource(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "event_sources"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # api, csv, webhook
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(
        "is_active",
        default=True,
        nullable=False,
    )

    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="source", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<EventSource id={self.id} name={self.name} type={self.source_type}>"


class Event(Base, UUIDPrimaryKeyMixin):
    """Time-series event table — optimized for append-heavy workloads."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_org_timestamp", "organization_id", "timestamp"),
        Index("ix_events_org_name", "organization_id", "event_name"),
        Index("ix_events_timestamp", "timestamp"),
        {"postgresql_partition_by": "RANGE (timestamp)"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="events"
    )
    source: Mapped["EventSource | None"] = relationship(
        "EventSource", back_populates="events"
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.event_name} ts={self.timestamp}>"
