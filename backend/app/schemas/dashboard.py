from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SavedQueryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    query_config: Dict[str, Any]


class SavedQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    query_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DashboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False
    refresh_interval: Optional[int] = None  # seconds
    template_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    refresh_interval: Optional[int] = None
    layout: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    created_by_id: UUID
    name: str
    description: Optional[str] = None
    is_public: bool
    public_slug: Optional[str] = None
    layout: Dict[str, Any]
    refresh_interval: Optional[int] = None
    template_type: Optional[str] = None
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class DashboardWithWidgets(DashboardResponse):
    widgets: List["WidgetResponse"] = Field(default_factory=list)


# Forward ref resolved after widget schema is imported
from app.schemas.widget import WidgetResponse  # noqa: E402

DashboardWithWidgets.model_rebuild()
