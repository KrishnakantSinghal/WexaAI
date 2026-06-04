from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, status

from app.core.dependencies import CurrentOrgID, CurrentUserID, DBSession
from app.schemas.common import MessageResponse
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    DashboardWithWidgets,
    SavedQueryCreate,
    SavedQueryResponse,
)
from app.schemas.widget import WidgetCreate, WidgetResponse, WidgetUpdate
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.post("", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    data: DashboardCreate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    return await service.create_dashboard(uuid.UUID(org_id), uuid.UUID(user_id), data)


@router.get("", response_model=List[DashboardResponse])
async def list_dashboards(
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
    skip: int = 0,
    limit: int = 50,
):
    service = DashboardService(db)
    return await service.get_dashboards(
        uuid.UUID(org_id), uuid.UUID(user_id), skip, limit
    )


@router.get("/public/{slug}", response_model=DashboardWithWidgets)
async def get_public_dashboard(slug: str, db: DBSession):
    service = DashboardService(db)
    return await service.get_public_dashboard(slug)


@router.get("/{dashboard_id}", response_model=DashboardWithWidgets)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    return await service.get_dashboard(
        dashboard_id, uuid.UUID(org_id), uuid.UUID(user_id)
    )


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    data: DashboardUpdate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    return await service.update_dashboard(
        dashboard_id, uuid.UUID(org_id), uuid.UUID(user_id), data
    )


@router.delete("/{dashboard_id}", response_model=MessageResponse)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    await service.delete_dashboard(dashboard_id, uuid.UUID(org_id), uuid.UUID(user_id))
    return MessageResponse(message="Dashboard deleted")


# --- Widgets ---


@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=201)
async def add_widget(
    dashboard_id: uuid.UUID,
    data: WidgetCreate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    return await service.add_widget(
        dashboard_id, uuid.UUID(org_id), uuid.UUID(user_id), data
    )


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    data: WidgetUpdate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    return await service.update_widget(
        widget_id, dashboard_id, uuid.UUID(org_id), uuid.UUID(user_id), data
    )


@router.delete("/{dashboard_id}/widgets/{widget_id}", response_model=MessageResponse)
async def delete_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    await service.delete_widget(
        widget_id, dashboard_id, uuid.UUID(org_id), uuid.UUID(user_id)
    )
    return MessageResponse(message="Widget deleted")


# --- Saved Queries ---


@router.post("/queries/saved", response_model=SavedQueryResponse, status_code=201)
async def create_saved_query(
    data: SavedQueryCreate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = DashboardService(db)
    return await service.create_saved_query(uuid.UUID(org_id), uuid.UUID(user_id), data)


@router.get("/queries/saved", response_model=List[SavedQueryResponse])
async def list_saved_queries(
    org_id: CurrentOrgID, user_id: CurrentUserID, db: DBSession
):
    from app.repositories.dashboard_repository import SavedQueryRepository

    service = DashboardService(db)
    await service._check_member(uuid.UUID(org_id), uuid.UUID(user_id), "viewer")
    repo = SavedQueryRepository(db)
    return await repo.get_org_queries(uuid.UUID(org_id))
