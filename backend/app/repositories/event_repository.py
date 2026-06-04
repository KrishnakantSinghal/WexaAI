from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventSource
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Event, session)

    async def bulk_insert(self, events: List[Event]) -> int:
        self.session.add_all(events)
        await self.session.flush()
        return len(events)

    async def query_events(
        self,
        org_id: UUID,
        start_time: datetime,
        end_time: datetime,
        event_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[Event]:
        stmt = select(Event).where(
            Event.organization_id == org_id,
            Event.timestamp >= start_time,
            Event.timestamp <= end_time,
        )
        if event_name:
            stmt = stmt.where(Event.event_name == event_name)
        stmt = stmt.order_by(Event.timestamp.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def aggregate_events(
        self,
        org_id: UUID,
        start_time: datetime,
        end_time: datetime,
        event_name: Optional[str],
        aggregation: str,
        time_bucket: str,
        group_by: Optional[str] = None,
        property_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build a time-bucketed aggregation query."""
        bucket_map = {
            "1m": "1 minute",
            "5m": "5 minutes",
            "15m": "15 minutes",
            "1h": "1 hour",
            "1d": "1 day",
            "1w": "1 week",
        }
        interval = bucket_map.get(time_bucket, "1 hour")

        # Build raw SQL for time_bucket aggregation (uses date_trunc as fallback)
        trunc_expr = f"date_trunc('{interval.split()[1]}', timestamp)"
        if aggregation == "count":
            agg_expr = "COUNT(*)"
        elif aggregation == "unique":
            agg_expr = "COUNT(DISTINCT user_id)"
        elif aggregation in ("sum", "avg", "min", "max"):
            prop = property_name or "value"
            agg_expr = f"{aggregation.upper()}(CAST(properties->>'{prop}' AS FLOAT))"
        else:
            agg_expr = "COUNT(*)"

        base_where = [
            f"organization_id = '{org_id}'",
            f"timestamp >= '{start_time.isoformat()}'",
            f"timestamp <= '{end_time.isoformat()}'",
        ]
        if event_name:
            base_where.append(f"event_name = '{event_name}'")

        where_clause = " AND ".join(base_where)
        select_clause = f"{trunc_expr} AS bucket, {agg_expr} AS value"
        group_clause = f"GROUP BY bucket ORDER BY bucket ASC"

        raw_sql = (
            f"SELECT {select_clause} FROM events WHERE {where_clause} {group_clause}"
        )
        result = await self.session.execute(text(raw_sql))
        rows = result.fetchall()
        return [{"bucket": str(row[0]), "value": row[1]} for row in rows]

    async def get_event_names(self, org_id: UUID) -> List[str]:
        result = await self.session.execute(
            select(func.distinct(Event.event_name)).where(
                Event.organization_id == org_id
            )
        )
        return list(result.scalars().all())


class EventSourceRepository(BaseRepository[EventSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EventSource, session)

    async def get_org_sources(self, org_id: UUID) -> List[EventSource]:
        result = await self.session.execute(
            select(EventSource).where(
                EventSource.organization_id == org_id,
                EventSource.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
