from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Header, Request, UploadFile, status

from app.core.dependencies import CurrentOrgID, CurrentUserID, DBSession
from app.core.exceptions import AuthenticationError, NotFoundError
from app.schemas.common import MessageResponse
from app.schemas.event import (
    BatchEventIngest,
    EventIngest,
    EventQueryRequest,
    EventQueryResult,
    EventResponse,
    EventSourceCreate,
    EventSourceResponse,
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single_event(
    data: EventIngest,
    request: Request,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = EventService(db)
    event = await service.ingest_single(
        org_id=uuid.UUID(org_id),
        data=data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"id": str(event.id), "status": "accepted"}


@router.post("/ingest/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_events(
    data: BatchEventIngest,
    request: Request,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = EventService(db)
    count = await service.ingest_batch(
        org_id=uuid.UUID(org_id),
        data=data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"ingested": count, "status": "accepted"}


@router.post("/ingest/csv", status_code=status.HTTP_202_ACCEPTED)
async def ingest_csv(
    file: UploadFile = File(...),
    org_id: CurrentOrgID = None,
    user_id: CurrentUserID = None,
    db: DBSession = None,
):
    if not file.content_type in ("text/csv", "application/csv", "text/plain"):
        from app.core.exceptions import ValidationError

        raise ValidationError("File must be a CSV")
    service = EventService(db)
    count = await service.ingest_csv(org_id=uuid.UUID(org_id), file=file)
    return {"ingested": count, "status": "accepted"}


@router.post("/query", response_model=EventQueryResult)
async def query_events(
    data: EventQueryRequest,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    service = EventService(db)
    return await service.query_events(org_id=uuid.UUID(org_id), query=data)


@router.get("/names", response_model=List[str])
async def get_event_names(org_id: CurrentOrgID, user_id: CurrentUserID, db: DBSession):
    service = EventService(db)
    return await service.get_event_names(org_id=uuid.UUID(org_id))


# --- Event Sources ---


@router.post("/sources", response_model=EventSourceResponse, status_code=201)
async def create_source(
    data: EventSourceCreate,
    org_id: CurrentOrgID,
    user_id: CurrentUserID,
    db: DBSession,
):
    from app.models.event import EventSource
    from app.repositories.event_repository import EventSourceRepository

    repo = EventSourceRepository(db)
    source = EventSource(
        organization_id=uuid.UUID(org_id),
        name=data.name,
        source_type=data.source_type,
        description=data.description,
        config=data.config,
    )
    await repo.create(source)
    return source


@router.get("/sources", response_model=List[EventSourceResponse])
async def list_sources(org_id: CurrentOrgID, user_id: CurrentUserID, db: DBSession):
    from app.repositories.event_repository import EventSourceRepository

    repo = EventSourceRepository(db)
    return await repo.get_org_sources(uuid.UUID(org_id))
