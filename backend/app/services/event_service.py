from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.event import Event, EventSource
from app.repositories.event_repository import EventRepository, EventSourceRepository
from app.schemas.event import BatchEventIngest, EventIngest, EventQueryRequest

logger = get_logger(__name__)


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.event_repo = EventRepository(session)
        self.source_repo = EventSourceRepository(session)

    async def ingest_single(
        self,
        org_id: uuid.UUID,
        data: EventIngest,
        source_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Event:
        now = datetime.now(timezone.utc)
        event = Event(
            organization_id=org_id,
            source_id=source_id,
            event_name=data.event_name,
            timestamp=data.timestamp or now,
            properties=data.properties,
            user_id=data.user_id,
            session_id=data.session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
        )
        await self.event_repo.create(event)
        logger.debug("event_ingested", event_name=data.event_name, org_id=str(org_id))
        return event

    async def ingest_batch(
        self,
        org_id: uuid.UUID,
        data: BatchEventIngest,
        source_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        now = datetime.now(timezone.utc)
        events = [
            Event(
                organization_id=org_id,
                source_id=source_id,
                event_name=e.event_name,
                timestamp=e.timestamp or now,
                properties=e.properties,
                user_id=e.user_id,
                session_id=e.session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=now,
            )
            for e in data.events
        ]
        count = await self.event_repo.bulk_insert(events)
        logger.info("batch_events_ingested", count=count, org_id=str(org_id))
        return count

    async def ingest_csv(
        self,
        org_id: uuid.UUID,
        file: UploadFile,
        source_id: Optional[uuid.UUID] = None,
    ) -> int:
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("CSV file must be UTF-8 encoded")

        reader = csv.DictReader(io.StringIO(text))
        required = {"event_name", "timestamp"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValidationError(
                "CSV must contain 'event_name' and 'timestamp' columns"
            )

        now = datetime.now(timezone.utc)
        events = []
        for i, row in enumerate(reader):
            if i >= 10000:
                raise ValidationError("CSV cannot exceed 10,000 rows")
            try:
                ts = datetime.fromisoformat(row["timestamp"])
            except ValueError:
                raise ValidationError(
                    f"Invalid timestamp on row {i + 2}: {row['timestamp']}"
                )

            reserved = {"event_name", "timestamp", "user_id", "session_id"}
            props = {k: v for k, v in row.items() if k not in reserved and v}

            events.append(
                Event(
                    organization_id=org_id,
                    source_id=source_id,
                    event_name=row["event_name"],
                    timestamp=ts,
                    properties=props,
                    user_id=row.get("user_id"),
                    session_id=row.get("session_id"),
                    created_at=now,
                )
            )

        count = await self.event_repo.bulk_insert(events)
        logger.info("csv_events_ingested", count=count, org_id=str(org_id))
        return count

    async def query_events(
        self, org_id: uuid.UUID, query: EventQueryRequest
    ) -> Dict[str, Any]:
        data = await self.event_repo.aggregate_events(
            org_id=org_id,
            start_time=query.start_time,
            end_time=query.end_time,
            event_name=query.event_name,
            aggregation=query.aggregation,
            time_bucket=query.time_bucket or "1h",
            group_by=query.group_by,
            property_name=query.property_name,
            filters=query.filters,
        )
        return {
            "data": data,
            "total": len(data),
            "query": query.model_dump(),
        }

    async def get_event_names(self, org_id: uuid.UUID) -> List[str]:
        return await self.event_repo.get_event_names(org_id)
