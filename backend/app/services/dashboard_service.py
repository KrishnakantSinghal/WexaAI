from __future__ import annotations

import secrets
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models.dashboard import Dashboard, SavedQuery
from app.models.widget import Widget
from app.repositories.dashboard_repository import (
    DashboardRepository,
    SavedQueryRepository,
    WidgetRepository,
)
from app.repositories.organization_repository import OrganizationMemberRepository
from app.schemas.dashboard import DashboardCreate, DashboardUpdate, SavedQueryCreate
from app.schemas.widget import WidgetCreate, WidgetUpdate

logger = get_logger(__name__)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.dashboard_repo = DashboardRepository(session)
        self.widget_repo = WidgetRepository(session)
        self.query_repo = SavedQueryRepository(session)
        self.member_repo = OrganizationMemberRepository(session)

    async def create_dashboard(
        self, org_id: uuid.UUID, user_id: uuid.UUID, data: DashboardCreate
    ) -> Dashboard:
        await self._check_member(org_id, user_id, min_role="analyst")
        public_slug = secrets.token_urlsafe(12) if data.is_public else None
        dashboard = Dashboard(
            organization_id=org_id,
            created_by_id=user_id,
            name=data.name,
            description=data.description,
            is_public=data.is_public,
            public_slug=public_slug,
            refresh_interval=data.refresh_interval,
            template_type=data.template_type,
            tags=data.tags,
            layout={},
        )
        return await self.dashboard_repo.create(dashboard)

    async def get_dashboards(
        self, org_id: uuid.UUID, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[Dashboard]:
        await self._check_member(org_id, user_id, min_role="viewer")
        return await self.dashboard_repo.get_org_dashboards(org_id, skip, limit)

    async def get_dashboard(
        self, dashboard_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dashboard:
        await self._check_member(org_id, user_id, min_role="viewer")
        dash = await self.dashboard_repo.get_with_widgets(dashboard_id)
        if not dash or dash.organization_id != org_id:
            raise NotFoundError("Dashboard")
        return dash

    async def get_public_dashboard(self, slug: str) -> Dashboard:
        dash = await self.dashboard_repo.get_by_public_slug(slug)
        if not dash:
            raise NotFoundError("Dashboard")
        return dash

    async def update_dashboard(
        self,
        dashboard_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: DashboardUpdate,
    ) -> Dashboard:
        await self._check_member(org_id, user_id, min_role="analyst")
        dash = await self.dashboard_repo.get_by_id(dashboard_id)
        if not dash or dash.organization_id != org_id:
            raise NotFoundError("Dashboard")

        update_data = data.model_dump(exclude_none=True)
        if update_data.get("is_public") and not dash.public_slug:
            update_data["public_slug"] = secrets.token_urlsafe(12)
        elif update_data.get("is_public") is False:
            update_data["public_slug"] = None

        return await self.dashboard_repo.update(dash, update_data)

    async def delete_dashboard(
        self, dashboard_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._check_member(org_id, user_id, min_role="admin")
        dash = await self.dashboard_repo.get_by_id(dashboard_id)
        if not dash or dash.organization_id != org_id:
            raise NotFoundError("Dashboard")
        await self.dashboard_repo.soft_delete(dash)

    # --- Widgets ---

    async def add_widget(
        self,
        dashboard_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: WidgetCreate,
    ) -> Widget:
        await self._check_member(org_id, user_id, min_role="analyst")
        dash = await self.dashboard_repo.get_by_id(dashboard_id)
        if not dash or dash.organization_id != org_id:
            raise NotFoundError("Dashboard")

        widget = Widget(
            dashboard_id=dashboard_id,
            saved_query_id=data.saved_query_id,
            title=data.title,
            widget_type=data.widget_type,
            config=data.config,
            position=data.position,
        )
        return await self.widget_repo.create(widget)

    async def update_widget(
        self,
        widget_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: WidgetUpdate,
    ) -> Widget:
        await self._check_member(org_id, user_id, min_role="analyst")
        widget = await self.widget_repo.get_by_id(widget_id)
        if not widget or widget.dashboard_id != dashboard_id:
            raise NotFoundError("Widget")
        return await self.widget_repo.update(widget, data.model_dump(exclude_none=True))

    async def delete_widget(
        self,
        widget_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._check_member(org_id, user_id, min_role="analyst")
        widget = await self.widget_repo.get_by_id(widget_id)
        if not widget or widget.dashboard_id != dashboard_id:
            raise NotFoundError("Widget")
        await self.widget_repo.soft_delete(widget)

    # --- Saved Queries ---

    async def create_saved_query(
        self, org_id: uuid.UUID, user_id: uuid.UUID, data: SavedQueryCreate
    ) -> SavedQuery:
        await self._check_member(org_id, user_id, min_role="analyst")
        query = SavedQuery(
            organization_id=org_id,
            created_by_id=user_id,
            name=data.name,
            description=data.description,
            query_config=data.query_config,
        )
        return await self.query_repo.create(query)

    async def _check_member(
        self, org_id: uuid.UUID, user_id: uuid.UUID, min_role: str
    ) -> None:
        hierarchy = {"viewer": 0, "analyst": 1, "admin": 2, "owner": 3}
        membership = await self.member_repo.get_membership(org_id, user_id)
        if not membership:
            raise AuthorizationError("Not a member of this organization")
        if hierarchy.get(membership.role, 0) < hierarchy.get(min_role, 0):
            raise AuthorizationError(f"Requires at least '{min_role}' role")
