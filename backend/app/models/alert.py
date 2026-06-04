from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "alerts"

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
    # Rule definition
    metric_query: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # { event_name, aggregation, filters, time_window_minutes }
    condition: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # gt, lt, gte, lte, eq
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    evaluation_interval_minutes: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )
    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active, triggered, resolved, muted
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    muted_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="alerts"
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    history: Mapped[list["AlertHistory"]] = relationship(
        "AlertHistory", back_populates="alert", lazy="select"
    )
    notification_channels: Mapped[list["AlertNotificationChannel"]] = relationship(
        "AlertNotificationChannel",
        back_populates="alert",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id} name={self.name} status={self.status}>"


class AlertHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "alert_history"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    triggered_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="history")


class AlertNotificationChannel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "alert_notification_channels"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # email, webhook, in_app
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # email: {to: [...]}, webhook: {url, headers}, in_app: {}

    alert: Mapped["Alert"] = relationship(
        "Alert", back_populates="notification_channels"
    )
