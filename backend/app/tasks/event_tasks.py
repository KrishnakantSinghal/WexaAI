from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.tasks.event_tasks.process_event_batch",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_event_batch(
    self, org_id: str, events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Background task to process and persist a batch of events.
    Used when the ingestion endpoint offloads heavy processing.
    """
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.event import Event
        from datetime import datetime, timezone
        import uuid

        async def _process():
            async with AsyncSessionLocal() as session:
                now = datetime.now(timezone.utc)
                db_events = [
                    Event(
                        organization_id=uuid.UUID(org_id),
                        event_name=e["event_name"],
                        timestamp=datetime.fromisoformat(
                            e.get("timestamp") or now.isoformat()
                        ),
                        properties=e.get("properties", {}),
                        user_id=e.get("user_id"),
                        session_id=e.get("session_id"),
                        created_at=now,
                    )
                    for e in events
                ]
                session.add_all(db_events)
                await session.commit()
                return len(db_events)

        count = asyncio.run(_process())
        logger.info("event_batch_processed", count=count, org_id=org_id)
        return {"processed": count}
    except Exception as exc:
        logger.error("event_batch_failed", error=str(exc), org_id=org_id)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.event_tasks.cleanup_old_events",
    bind=True,
)
def cleanup_old_events(self, org_id: str, days_to_keep: int = 365) -> Dict[str, Any]:
    """Enforce data retention policy by deleting old events."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.event import Event
        from sqlalchemy import delete
        from datetime import datetime, timezone, timedelta

        async def _cleanup():
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    delete(Event).where(
                        Event.organization_id == org_id,
                        Event.timestamp < cutoff,
                    )
                )
                await session.commit()
                return result.rowcount

        deleted = asyncio.run(_cleanup())
        logger.info("events_cleaned", deleted=deleted, org_id=org_id)
        return {"deleted": deleted}
    except Exception as exc:
        logger.error("event_cleanup_failed", error=str(exc))
        raise self.retry(exc=exc)
