from __future__ import annotations

from fastapi import HTTPException, status

try:
    HTTP_422_VALIDATION = status.HTTP_422_UNPROCESSABLE_CONTENT
except AttributeError:  # pragma: no cover - compatibility with older FastAPI
    HTTP_422_VALIDATION = status.HTTP_422_UNPROCESSABLE_ENTITY


class AppError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(AppError):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=HTTP_422_VALIDATION)


class AuthError(AppError):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)
