from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Response
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import TokenResponse, UserCreate
from app.config import settings
from app.shared.errors import AuthError, ValidationError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def get_token_version(user: User) -> int:
    return int(getattr(user, "token_version", 0) or 0)


def create_access_token(user_id: str, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {
            "sub": user_id,
            "exp": expire,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "ver": token_version,
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(user_id: str, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
            "ver": token_version,
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_tokens(user_id: str, token_version: int = 0) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id, token_version=token_version),
        refresh_token=create_refresh_token(user_id, token_version=token_version),
    )


def decode_token_payload(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_type = payload.get("type")
        if expected_type is not None and token_type != expected_type:
            raise AuthError("Invalid token type")
        if payload.get("sub") is None:
            raise AuthError("Invalid token")
        return payload
    except InvalidTokenError:
        raise AuthError("Invalid token")


def decode_refresh_token(token: str) -> str:
    payload = decode_token_payload(token, expected_type="refresh")
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthError("Invalid refresh token")
    return user_id


def set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    response.set_cookie(
        key=settings.access_cookie_name,
        value=tokens.access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.access_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise ValidationError("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password")
    if not user.is_active:
        raise AuthError("User is inactive")
    return user
