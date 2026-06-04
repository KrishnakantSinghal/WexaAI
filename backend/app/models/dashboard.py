from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class SavedQuery(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "saved_queries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # query_config: { event_name, aggregation, group_by, filters, time_range }

    widgets: Mapped[list["Widget"]] = relationship(
        "Widget", back_populates="saved_query", lazy="select"
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<SavedQuery id={self.id} name={self.name}>"


class Dashboard(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "dashboards"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_slug: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    layout: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # layout: grid positions for widgets
    refresh_interval: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # seconds: 30, 60, 300
    template_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # web_analytics, sales, devops
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="dashboards"
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    widgets: Mapped[list["Widget"]] = relationship(
        "Widget",
        back_populates="dashboard",
        lazy="select",
        cascade="all, delete-orphan",
    )
    report_schedules: Mapped[list["ReportSchedule"]] = relationship(
        "ReportSchedule", back_populates="dashboard", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} name={self.name}>"
