from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationChannelConfig(BaseModel):
    channel_type: str = Field(pattern="^(email|webhook|in_app)$")
    config: Dict[str, Any] = Field(default_factory=dict)


class AlertCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    metric_query: Dict[str, Any]
    condition: str = Field(pattern="^(gt|lt|gte|lte|eq)$")
    threshold: float
    evaluation_interval_minutes: int = Field(default=5, ge=1, le=1440)
    notification_channels: List[NotificationChannelConfig] = Field(default_factory=list)


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metric_query: Optional[Dict[str, Any]] = None
    condition: Optional[str] = Field(None, pattern="^(gt|lt|gte|lte|eq)$")
    threshold: Optional[float] = None
    evaluation_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    metric_query: Dict[str, Any]
    condition: str
    threshold: float
    evaluation_interval_minutes: int
    status: str
    last_evaluated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    muted_until: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AlertHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    triggered_value: float
    threshold: float
    message: Optional[str] = None


class MuteAlertRequest(BaseModel):
    mute_until: datetime
