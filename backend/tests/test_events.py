from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "SecurePass1",
            "full_name": "Event Tester",
            "organization_name": "Event Org",
        },
    )
    resp = await client.post(
        "/api/v1/auth/signin",
        json={"email": email, "password": "SecurePass1"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_ingest_single_event(client: AsyncClient):
    token = await _get_token(client, "events@example.com")
    response = await client.post(
        "/api/v1/events/ingest",
        json={"event_name": "page_view", "properties": {"url": "/home"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_ingest_batch_events(client: AsyncClient):
    token = await _get_token(client, "batch@example.com")
    response = await client.post(
        "/api/v1/events/ingest/batch",
        json={
            "events": [
                {"event_name": "click", "properties": {"button": "cta"}},
                {"event_name": "purchase", "properties": {"amount": 99.99}},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202
    assert response.json()["ingested"] == 2
