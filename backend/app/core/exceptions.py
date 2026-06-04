from __future__ import annotations

from http import HTTPStatus
from typing import Any, Optional

from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code or "INTERNAL_ERROR"
        self.details = details
        super().__init__(message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTHORIZATION_ERROR",
        )


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
        )


class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details=details,
        )


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
        )


class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message=message)
        self.code = "INVALID_TOKEN"
