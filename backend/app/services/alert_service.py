from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models.alert import Alert, AlertHistory, AlertNotificationChannel
from app.repositories.alert_repository import AlertHistoryRepository, AlertRepository
from app.repositories.organization_repository import OrganizationMemberRepository
from app.schemas.alert import AlertCreate, AlertUpdate, MuteAlertRequest

logger = get_logger(__name__)


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.alert_repo = AlertRepository(session)
        self.history_repo = AlertHistoryRepository(session)
        self.member_repo = OrganizationMemberRepository(session)

    async def create_alert(
        self, org_id: uuid.UUID, user_id: uuid.UUID, data: AlertCreate
    ) -> Alert:
        await self._check_member(org_id, user_id, "analyst")
        alert = Alert(
            organization_id=org_id,
            created_by_id=user_id,
            name=data.name,
            description=data.description,
            metric_query=data.metric_query,
            condition=data.condition,
            threshold=data.threshold,
            evaluation_interval_minutes=data.evaluation_interval_minutes,
            status="active",
        )
        await self.alert_repo.create(alert)

        for ch in data.notification_channels:
            channel = AlertNotificationChannel(
                alert_id=alert.id,
                channel_type=ch.channel_type,
                config=ch.config,
            )
            self.session.add(channel)
        await self.session.flush()

        logger.info("alert_created", alert_id=str(alert.id), org_id=str(org_id))
        return alert

    async def get_alerts(
        self, org_id: uuid.UUID, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[Alert]:
        await self._check_member(org_id, user_id, "viewer")
        return await self.alert_repo.get_org_alerts(org_id, skip, limit)

    async def get_alert(
        self, alert_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> Alert:
        await self._check_member(org_id, user_id, "viewer")
        alert = await self.alert_repo.get_with_channels(alert_id)
        if not alert or alert.organization_id != org_id:
            raise NotFoundError("Alert")
        return alert

    async def update_alert(
        self,
        alert_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: AlertUpdate,
    ) -> Alert:
        await self._check_member(org_id, user_id, "analyst")
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert or alert.organization_id != org_id:
            raise NotFoundError("Alert")
        return await self.alert_repo.update(alert, data.model_dump(exclude_none=True))

    async def delete_alert(
        self, alert_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._check_member(org_id, user_id, "admin")
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert or alert.organization_id != org_id:
            raise NotFoundError("Alert")
        await self.alert_repo.soft_delete(alert)

    async def mute_alert(
        self,
        alert_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MuteAlertRequest,
    ) -> Alert:
        await self._check_member(org_id, user_id, "analyst")
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert or alert.organization_id != org_id:
            raise NotFoundError("Alert")
        return await self.alert_repo.update(
            alert, {"status": "muted", "muted_until": data.mute_until}
        )

    async def unmute_alert(
        self, alert_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> Alert:
        await self._check_member(org_id, user_id, "analyst")
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert or alert.organization_id != org_id:
            raise NotFoundError("Alert")
        return await self.alert_repo.update(
            alert, {"status": "active", "muted_until": None}
        )

    async def get_history(
        self, alert_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[AlertHistory]:
        await self._check_member(org_id, user_id, "viewer")
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert or alert.organization_id != org_id:
            raise NotFoundError("Alert")
        return await self.history_repo.get_alert_history(alert_id)

    async def _check_member(
        self, org_id: uuid.UUID, user_id: uuid.UUID, min_role: str
    ) -> None:
        hierarchy = {"viewer": 0, "analyst": 1, "admin": 2, "owner": 3}
        membership = await self.member_repo.get_membership(org_id, user_id)
        if not membership:
            raise AuthorizationError("Not a member of this organization")
        if hierarchy.get(membership.role, 0) < hierarchy.get(min_role, 0):
            raise AuthorizationError(f"Requires at least '{min_role}' role")
