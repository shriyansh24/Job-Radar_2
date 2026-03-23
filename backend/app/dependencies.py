from __future__ import annotations

import uuid as uuid_mod
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import decode_token_payload, get_token_version
from app.config import Settings, settings
from app.database import async_session_factory
from app.shared.errors import AuthError

if TYPE_CHECKING:
    from app.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@lru_cache
def get_settings() -> Settings:
    return settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> "User":
    from app.auth.models import User

    access_token = token or request.cookies.get(settings.access_cookie_name)
    if not access_token:
        raise AuthError("Authentication required")

    payload = decode_token_payload(access_token, expected_type="access")
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthError("Invalid token")

    result = await db.execute(select(User).where(User.id == uuid_mod.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("User not found")
    if not user.is_active:
        raise AuthError("User is inactive")
    if int(payload.get("ver", 0)) != get_token_version(user):
        raise AuthError("Token revoked")
    return user
