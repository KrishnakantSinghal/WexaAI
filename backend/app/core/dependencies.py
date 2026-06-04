from __future__ import annotations

from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
)
from app.core.security import decode_token
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
) -> str:
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()
        return user_id
    except JWTError:
        raise InvalidTokenError()


async def get_current_org_id(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
) -> Optional[str]:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return payload.get("org_id")
    except JWTError:
        return None


async def get_current_user_role(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
) -> Optional[str]:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return payload.get("role")
    except JWTError:
        return None


class RoleChecker:
    """Dependency that enforces minimum role requirement."""

    ROLE_HIERARCHY = {
        "viewer": 0,
        "analyst": 1,
        "admin": 2,
        "owner": 3,
    }

    def __init__(self, minimum_role: str) -> None:
        self.minimum_role = minimum_role.lower()

    def __call__(
        self,
        role: Annotated[Optional[str], Depends(get_current_user_role)],
    ) -> None:
        if not role:
            raise AuthorizationError("Role not found in token")
        user_level = self.ROLE_HIERARCHY.get(role.lower(), -1)
        required_level = self.ROLE_HIERARCHY.get(self.minimum_role, 0)
        if user_level < required_level:
            raise AuthorizationError(
                f"Requires at least '{self.minimum_role}' role, got '{role}'"
            )


require_viewer = RoleChecker("viewer")
require_analyst = RoleChecker("analyst")
require_admin = RoleChecker("admin")
require_owner = RoleChecker("owner")

# Typed dependency aliases
CurrentUserID = Annotated[str, Depends(get_current_user_id)]
CurrentOrgID = Annotated[Optional[str], Depends(get_current_org_id)]
CurrentUserRole = Annotated[Optional[str], Depends(get_current_user_role)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
