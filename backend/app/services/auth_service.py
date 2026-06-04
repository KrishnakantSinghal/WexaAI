from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    InvalidTokenError,
    NotFoundError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_invite_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.repositories.organization_repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SignInRequest, SignUpRequest, TokenResponse

logger = get_logger(__name__)


def _slugify(name: str) -> str:
    import re

    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug[:100]


async def _unique_slug(org_repo: OrganizationRepository, base: str) -> str:
    slug = _slugify(base)
    if not await org_repo.slug_exists(slug):
        return slug
    for i in range(1, 100):
        candidate = f"{slug}-{i}"
        if not await org_repo.slug_exists(candidate):
            return candidate
    return f"{slug}-{uuid.uuid4().hex[:8]}"


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)
        self.member_repo = OrganizationMemberRepository(session)

    async def sign_up(
        self, data: SignUpRequest
    ) -> Tuple[User, Organization, TokenResponse]:
        if await self.user_repo.email_exists(data.email):
            raise ConflictError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_verified=True,  # simplify: auto-verify
        )
        await self.user_repo.create(user)

        slug = await _unique_slug(self.org_repo, data.organization_name)
        org = Organization(name=data.organization_name, slug=slug)
        await self.org_repo.create(org)

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        )
        await self.member_repo.create(member)

        tokens = self._generate_tokens(user, org, "owner")
        logger.info("user_signed_up", user_id=str(user.id), org_id=str(org.id))
        return user, org, tokens

    async def sign_in(self, data: SignInRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not user.hashed_password:
            raise AuthenticationError("Invalid credentials")
        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Get primary org
        orgs = await self.org_repo.get_user_organizations(user.id)
        org = orgs[0] if orgs else None
        role = "viewer"
        if org:
            membership = await self.member_repo.get_membership(org.id, user.id)
            role = membership.role if membership else "viewer"

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()

        tokens = self._generate_tokens(user, org, role)
        logger.info("user_signed_in", user_id=str(user.id))
        return tokens

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise InvalidTokenError()
            user_id = payload.get("sub")
            if not user_id:
                raise InvalidTokenError()
        except JWTError:
            raise InvalidTokenError()

        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        orgs = await self.org_repo.get_user_organizations(user.id)
        org = orgs[0] if orgs else None
        role = "viewer"
        if org:
            membership = await self.member_repo.get_membership(org.id, user.id)
            role = membership.role if membership else "viewer"

        return self._generate_tokens(user, org, role)

    def _generate_tokens(
        self,
        user: User,
        org: Optional[Organization],
        role: str,
    ) -> TokenResponse:
        access_token = create_access_token(
            subject=user.id,
            org_id=str(org.id) if org else None,
            role=role,
        )
        refresh_token = create_refresh_token(subject=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # type: ignore[call-arg]
        )
