from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.organization import Organization, OrganizationInvite, OrganizationMember
from app.models.api_key import ApiKey
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Organization, session)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.session.execute(
            select(Organization).where(
                Organization.slug == slug, Organization.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self.session.execute(
            select(Organization.id).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none() is not None

    async def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        result = await self.session.execute(
            select(Organization)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Organization.id,
            )
            .where(
                OrganizationMember.user_id == user_id,
                Organization.deleted_at.is_(None),
                Organization.is_active.is_(True),
            )
        )
        return list(result.scalars().all())


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(OrganizationMember, session)

    async def get_membership(
        self, org_id: UUID, user_id: UUID
    ) -> Optional[OrganizationMember]:
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_org_members(self, org_id: UUID) -> List[OrganizationMember]:
        from app.models.user import User

        result = await self.session.execute(
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == org_id)
        )
        return list(result.scalars().all())


class OrganizationInviteRepository(BaseRepository[OrganizationInvite]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(OrganizationInvite, session)

    async def get_by_token(self, token: str) -> Optional[OrganizationInvite]:
        result = await self.session.execute(
            select(OrganizationInvite).where(
                OrganizationInvite.token == token,
                OrganizationInvite.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()


class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApiKey, session)

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        result = await self.session.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active.is_(True),
                ApiKey.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_org_keys(self, org_id: UUID) -> List[ApiKey]:
        result = await self.session.execute(
            select(ApiKey).where(
                ApiKey.organization_id == org_id,
                ApiKey.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
