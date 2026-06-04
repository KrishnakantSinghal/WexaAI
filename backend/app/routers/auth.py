from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession
from app.schemas.auth import (
    AcceptInviteRequest,
    RefreshTokenRequest,
    SignInRequest,
    SignUpRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def sign_up(data: SignUpRequest, response: Response, db: DBSession):
    service = AuthService(db)
    user, org, tokens = await service.sign_up(data)
    _set_refresh_cookie(response, tokens.refresh_token)  # type: ignore[attr-defined]
    return tokens


@router.post("/signin", response_model=TokenResponse)
async def sign_in(data: SignInRequest, response: Response, db: DBSession):
    service = AuthService(db)
    tokens = await service.sign_in(data)
    _set_refresh_cookie(response, tokens.refresh_token)  # type: ignore[attr-defined]
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: Request, response: Response, db: DBSession):
    # Accept token from cookie or body
    cookie_token = request.cookies.get("refresh_token")
    body: dict = {}
    try:
        body = await request.json()
    except Exception:
        pass
    refresh_token = cookie_token or body.get("refresh_token", "")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    service = AuthService(db)
    tokens = await service.refresh_tokens(refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)  # type: ignore[attr-defined]
    return tokens


@router.post("/signout", response_model=MessageResponse)
async def sign_out(response: Response):
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Signed out successfully")


def _set_refresh_cookie(response: Response, token: str) -> None:
    from app.core.config import settings

    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/v1/auth/refresh",
    )
