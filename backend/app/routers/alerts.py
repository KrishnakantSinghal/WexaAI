from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, status

from app.core.dependencies import CurrentOrgID, CurrentUserID, DBSession
from app.schemas.alert import (
    AlertCreate,
    AlertHistoryResponse,
    AlertResponse,
    AlertUpdate,
    MuteAlertRequest,
)
from app.schemas.common import MessageResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    data: AlertCreate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    return await service.create_alert(uuid.UUID(org_id), uuid.UUID(user_id), data)


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
    skip: int = 0,
    limit: int = 50,
):
    service = AlertService(db)
    return await service.get_alerts(uuid.UUID(org_id), uuid.UUID(user_id), skip, limit)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    return await service.get_alert(alert_id, uuid.UUID(org_id), uuid.UUID(user_id))


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    data: AlertUpdate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    return await service.update_alert(
        alert_id, uuid.UUID(org_id), uuid.UUID(user_id), data
    )


@router.delete("/{alert_id}", response_model=MessageResponse)
async def delete_alert(
    alert_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    await service.delete_alert(alert_id, uuid.UUID(org_id), uuid.UUID(user_id))
    return MessageResponse(message="Alert deleted")


@router.post("/{alert_id}/mute", response_model=AlertResponse)
async def mute_alert(
    alert_id: uuid.UUID,
    data: MuteAlertRequest,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    return await service.mute_alert(
        alert_id, uuid.UUID(org_id), uuid.UUID(user_id), data
    )


@router.post("/{alert_id}/unmute", response_model=AlertResponse)
async def unmute_alert(
    alert_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    return await service.unmute_alert(alert_id, uuid.UUID(org_id), uuid.UUID(user_id))


@router.get("/{alert_id}/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    alert_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = AlertService(db)
    return await service.get_history(alert_id, uuid.UUID(org_id), uuid.UUID(user_id))
