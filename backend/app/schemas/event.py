from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventProperties(BaseModel):
    model_config = ConfigDict(extra="allow")


class EventIngest(BaseModel):
    event_name: str = Field(min_length=1, max_length=255)
    timestamp: Optional[datetime] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = Field(None, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)


class BatchEventIngest(BaseModel):
    events: List[EventIngest] = Field(min_length=1, max_length=1000)

    @field_validator("events")
    @classmethod
    def check_batch_size(cls, v: List[EventIngest]) -> List[EventIngest]:
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000 events")
        return v


class EventSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(pattern="^(api|csv|webhook)$")
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class EventSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    source_type: str
    description: Optional[str] = None
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    source_id: Optional[UUID] = None
    event_name: str
    timestamp: datetime
    properties: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime


class EventQueryRequest(BaseModel):
    event_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    aggregation: str = Field(
        default="count", pattern="^(count|sum|avg|min|max|unique)$"
    )
    group_by: Optional[str] = None
    property_name: Optional[str] = None  # for sum/avg/min/max
    filters: Dict[str, Any] = Field(default_factory=dict)
    time_bucket: Optional[str] = Field(default="1h", pattern="^(1m|5m|15m|1h|1d|1w)$")


class EventQueryResult(BaseModel):
    data: List[Dict[str, Any]]
    total: int
    query: Dict[str, Any]
