from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    created_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="viewer", pattern="^(owner|admin|analyst|viewer)$")


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str
    expires_at: datetime
    created_at: datetime


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(pattern="^(owner|admin|analyst|viewer)$")


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: str = Field(default="ingest", pattern="^(ingest|read|admin)$")
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned once on creation — includes the full key."""

    full_key: str
