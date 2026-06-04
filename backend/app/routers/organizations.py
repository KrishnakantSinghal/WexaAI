from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentOrgID, CurrentUserID, DBSession, require_admin
from app.core.exceptions import NotFoundError
from app.repositories.organization_repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.schemas.common import MessageResponse
from app.schemas.organization import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    InviteMemberRequest,
    InviteResponse,
    MemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateMemberRoleRequest,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _parse_org(org_id_str: str) -> uuid.UUID:
    try:
        return uuid.UUID(org_id_str)
    except ValueError:
        raise NotFoundError("Organization")


@router.get("/current", response_model=OrganizationResponse)
async def get_current_org(org_id: CurrentOrgID, db: DBSession):
    if not org_id:
        raise NotFoundError("Organization")
    repo = OrganizationRepository(db)
    org = await repo.get_by_id(uuid.UUID(org_id))
    if not org:
        raise NotFoundError("Organization")
    return org


@router.patch("/current", response_model=OrganizationResponse)
async def update_org(
    data: OrganizationUpdate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = OrganizationService(db)
    return await service.update_organization(
        uuid.UUID(org_id), data, uuid.UUID(user_id)
    )


@router.get("/current/members", response_model=List[MemberResponse])
async def list_members(org_id: CurrentOrgID, user_id: CurrentUserID, db: DBSession):
    service = OrganizationService(db)
    await service._require_role(uuid.UUID(org_id), uuid.UUID(user_id), "viewer")
    repo = OrganizationMemberRepository(db)
    members = await repo.get_org_members(uuid.UUID(org_id))
    return [
        MemberResponse(
            id=m.id,
            user_id=m.user_id,
            organization_id=m.organization_id,
            role=m.role,
            created_at=m.created_at,
            user_email=m.user.email if m.user else None,
            user_full_name=m.user.full_name if m.user else None,
        )
        for m in members
    ]


@router.post("/current/members/invite", response_model=InviteResponse, status_code=201)
async def invite_member(
    data: InviteMemberRequest,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = OrganizationService(db)
    invite = await service.invite_member(uuid.UUID(org_id), data, uuid.UUID(user_id))
    return invite


@router.patch("/current/members/{member_user_id}/role", response_model=MemberResponse)
async def update_member_role(
    member_user_id: uuid.UUID,
    data: UpdateMemberRoleRequest,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = OrganizationService(db)
    await service._require_role(uuid.UUID(org_id), uuid.UUID(user_id), "admin")
    repo = OrganizationMemberRepository(db)
    member = await repo.get_membership(uuid.UUID(org_id), member_user_id)
    if not member:
        raise NotFoundError("Member")
    updated = await repo.update(member, {"role": data.role})
    return MemberResponse(
        id=updated.id,
        user_id=updated.user_id,
        organization_id=updated.organization_id,
        role=updated.role,
        created_at=updated.created_at,
    )


# --- API Keys ---


@router.get("/current/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(org_id: CurrentOrgID, user_id: CurrentUserID, db: DBSession):
    from app.repositories.organization_repository import ApiKeyRepository

    service = OrganizationService(db)
    await service._require_role(uuid.UUID(org_id), uuid.UUID(user_id), "admin")
    repo = ApiKeyRepository(db)
    return await repo.get_org_keys(uuid.UUID(org_id))


@router.post(
    "/current/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=201,
)
async def create_api_key(
    data: ApiKeyCreate, org_id: CurrentOrgID, user_id: CurrentUserID, db: DBSession
):
    service = OrganizationService(db)
    api_key, full_key = await service.create_api_key(
        uuid.UUID(org_id), data, uuid.UUID(user_id)
    )
    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        full_key=full_key,
    )


@router.delete("/current/api-keys/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: uuid.UUID,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = OrganizationService(db)
    await service.revoke_api_key(key_id, uuid.UUID(org_id), uuid.UUID(user_id))
    return MessageResponse(message="API key revoked")
