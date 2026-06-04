from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ReportRecipient(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class ReportScheduleCreate(BaseModel):
    dashboard_id: UUID
    name: str = Field(min_length=1, max_length=255)
    frequency: str = Field(pattern="^(daily|weekly|monthly)$")
    recipients: List[ReportRecipient]
    format: str = Field(default="pdf", pattern="^(pdf|png)$")


class ReportScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    dashboard_id: UUID
    name: str
    frequency: str
    cron_expression: str
    recipients: List[Dict[str, Any]]
    format: str
    is_active: bool
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    schedule_id: Optional[UUID] = None
    dashboard_id: UUID
    status: str
    format: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None
    created_at: datetime
