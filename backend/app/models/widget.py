from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Widget(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "widgets"

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saved_query_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_queries.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    widget_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # line_chart, bar_chart, pie_chart, kpi_card, table
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # config: { colors, legend, axes, aggregation overrides, time_range }
    position: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # position: { x, y, w, h }  — grid layout coords

    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
    saved_query: Mapped["SavedQuery | None"] = relationship(
        "SavedQuery", back_populates="widgets"
    )

    def __repr__(self) -> str:
        return f"<Widget id={self.id} type={self.widget_type} dashboard={self.dashboard_id}>"
