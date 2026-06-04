from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_signup(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "SecurePass1",
            "full_name": "Test User",
            "organization_name": "Test Org",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "SecurePass1",
        "full_name": "Test User",
        "organization_name": "Test Org",
    }
    await client.post("/api/v1/auth/signup", json=payload)
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_signin(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "signin@example.com",
            "password": "SecurePass1",
            "full_name": "Signin User",
            "organization_name": "Signin Org",
        },
    )
    response = await client.post(
        "/api/v1/auth/signin",
        json={"email": "signin@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_signin_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrong@example.com",
            "password": "SecurePass1",
            "full_name": "Wrong User",
            "organization_name": "Wrong Org",
        },
    )
    response = await client.post(
        "/api/v1/auth/signin",
        json={"email": "wrong@example.com", "password": "WrongPass99"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    signup_resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "me@example.com",
            "password": "SecurePass1",
            "full_name": "Me User",
            "organization_name": "Me Org",
        },
    )
    token = signup_resp.json()["access_token"]
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
