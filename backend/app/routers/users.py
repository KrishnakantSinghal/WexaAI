from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import CurrentOrgID, CurrentUserID, DBSession
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: CurrentUserID, db: DBSession):
    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("User")
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(data: UserUpdate, user_id: CurrentUserID, db: DBSession):
    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("User")
    return await repo.update(user, data.model_dump(exclude_none=True))
