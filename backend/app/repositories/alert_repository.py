from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.alert import Alert, AlertHistory, AlertNotificationChannel
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Alert, session)

    async def get_org_alerts(
        self, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Alert]:
        result = await self.session.execute(
            select(Alert)
            .where(
                Alert.organization_id == org_id,
                Alert.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_alerts(self) -> List[Alert]:
        """Return all active alerts eligible for evaluation."""
        result = await self.session.execute(
            select(Alert)
            .options(joinedload(Alert.notification_channels))
            .where(
                Alert.is_active.is_(True),
                Alert.status != "muted",
                Alert.deleted_at.is_(None),
            )
        )
        return list(result.unique().scalars().all())

    async def get_with_channels(self, alert_id: UUID) -> Optional[Alert]:
        result = await self.session.execute(
            select(Alert)
            .options(joinedload(Alert.notification_channels))
            .where(Alert.id == alert_id, Alert.deleted_at.is_(None))
        )
        return result.unique().scalar_one_or_none()


class AlertHistoryRepository(BaseRepository[AlertHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AlertHistory, session)

    async def get_alert_history(
        self, alert_id: UUID, limit: int = 50
    ) -> List[AlertHistory]:
        result = await self.session.execute(
            select(AlertHistory)
            .where(AlertHistory.alert_id == alert_id)
            .order_by(AlertHistory.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
