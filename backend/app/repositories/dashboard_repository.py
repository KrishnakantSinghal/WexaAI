from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.dashboard import Dashboard, SavedQuery
from app.models.widget import Widget
from app.repositories.base import BaseRepository


class DashboardRepository(BaseRepository[Dashboard]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Dashboard, session)

    async def get_org_dashboards(
        self, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Dashboard]:
        result = await self.session.execute(
            select(Dashboard)
            .where(
                Dashboard.organization_id == org_id,
                Dashboard.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_widgets(self, dashboard_id: UUID) -> Optional[Dashboard]:
        result = await self.session.execute(
            select(Dashboard)
            .options(joinedload(Dashboard.widgets))
            .where(
                Dashboard.id == dashboard_id,
                Dashboard.deleted_at.is_(None),
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_by_public_slug(self, slug: str) -> Optional[Dashboard]:
        result = await self.session.execute(
            select(Dashboard).where(
                Dashboard.public_slug == slug,
                Dashboard.is_public.is_(True),
                Dashboard.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


class WidgetRepository(BaseRepository[Widget]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Widget, session)

    async def get_dashboard_widgets(self, dashboard_id: UUID) -> List[Widget]:
        result = await self.session.execute(
            select(Widget).where(
                Widget.dashboard_id == dashboard_id,
                Widget.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())


class SavedQueryRepository(BaseRepository[SavedQuery]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SavedQuery, session)

    async def get_org_queries(self, org_id: UUID) -> List[SavedQuery]:
        result = await self.session.execute(
            select(SavedQuery).where(
                SavedQuery.organization_id == org_id,
                SavedQuery.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
