from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.logging import get_logger
from app.core.security import generate_api_key, generate_invite_token, hash_password
from app.models.api_key import ApiKey
from app.models.organization import OrganizationInvite, OrganizationMember
from app.repositories.organization_repository import (
    ApiKeyRepository,
    OrganizationInviteRepository,
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.organization import (
    ApiKeyCreate,
    InviteMemberRequest,
    OrganizationCreate,
    OrganizationUpdate,
)

logger = get_logger(__name__)


def _slugify(name: str) -> str:
    import re

    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:100]


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.org_repo = OrganizationRepository(session)
        self.member_repo = OrganizationMemberRepository(session)
        self.invite_repo = OrganizationInviteRepository(session)
        self.api_key_repo = ApiKeyRepository(session)
        self.user_repo = UserRepository(session)

    async def get_org_or_404(self, org_id: uuid.UUID):
        org = await self.org_repo.get_by_id(org_id)
        if not org or org.deleted_at:
            raise NotFoundError("Organization")
        return org

    async def update_organization(
        self, org_id: uuid.UUID, data: OrganizationUpdate, requesting_user_id: uuid.UUID
    ):
        org = await self.get_org_or_404(org_id)
        await self._require_role(org_id, requesting_user_id, min_role="admin")
        update_data = data.model_dump(exclude_none=True)
        return await self.org_repo.update(org, update_data)

    async def invite_member(
        self,
        org_id: uuid.UUID,
        data: InviteMemberRequest,
        inviting_user_id: uuid.UUID,
    ) -> OrganizationInvite:
        await self._require_role(org_id, inviting_user_id, min_role="admin")

        existing = await self.member_repo.get_membership(
            org_id, uuid.UUID(str(inviting_user_id))
        )
        token = generate_invite_token()
        invite = OrganizationInvite(
            organization_id=org_id,
            email=data.email,
            role=data.role,
            token=token,
            invited_by_id=inviting_user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        return await self.invite_repo.create(invite)

    async def accept_invite(self, token: str, user_id: uuid.UUID) -> OrganizationMember:
        invite = await self.invite_repo.get_by_token(token)
        if (
            not invite
            or invite.accepted_at
            or invite.expires_at < datetime.now(timezone.utc)
        ):
            raise NotFoundError("Invite")

        existing = await self.member_repo.get_membership(
            invite.organization_id, user_id
        )
        if existing:
            raise ConflictError("Already a member of this organization")

        member = OrganizationMember(
            organization_id=invite.organization_id,
            user_id=user_id,
            role=invite.role,
        )
        await self.member_repo.create(member)

        invite.accepted_at = datetime.now(timezone.utc)
        invite.is_active = False
        await self.session.flush()
        return member

    async def create_api_key(
        self, org_id: uuid.UUID, data: ApiKeyCreate, user_id: uuid.UUID
    ) -> Tuple[ApiKey, str]:
        await self._require_role(org_id, user_id, min_role="admin")

        full_key = generate_api_key()
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_prefix = full_key[:12]

        api_key = ApiKey(
            organization_id=org_id,
            created_by_id=user_id,
            name=data.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=data.scopes,
            expires_at=data.expires_at,
        )
        api_key = await self.api_key_repo.create(api_key)
        return api_key, full_key

    async def revoke_api_key(
        self, key_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._require_role(org_id, user_id, min_role="admin")
        key = await self.api_key_repo.get_by_id(key_id)
        if not key or key.organization_id != org_id:
            raise NotFoundError("API Key")
        await self.api_key_repo.update(key, {"is_active": False})

    async def _require_role(
        self, org_id: uuid.UUID, user_id: uuid.UUID, min_role: str
    ) -> None:
        hierarchy = {"viewer": 0, "analyst": 1, "admin": 2, "owner": 3}
        membership = await self.member_repo.get_membership(org_id, user_id)
        if not membership:
            raise AuthorizationError("Not a member of this organization")
        user_level = hierarchy.get(membership.role, 0)
        required_level = hierarchy.get(min_role, 0)
        if user_level < required_level:
            raise AuthorizationError(f"Requires at least '{min_role}' role")
