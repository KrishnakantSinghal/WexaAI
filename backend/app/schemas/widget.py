from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WidgetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    widget_type: str = Field(
        pattern="^(line_chart|bar_chart|pie_chart|kpi_card|table)$"
    )
    saved_query_id: Optional[UUID] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, int] = Field(
        default_factory=lambda: {"x": 0, "y": 0, "w": 6, "h": 4}
    )


class WidgetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    saved_query_id: Optional[UUID] = None
    config: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, int]] = None


class WidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dashboard_id: UUID
    saved_query_id: Optional[UUID] = None
    title: str
    widget_type: str
    config: Dict[str, Any]
    position: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
