from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import cast

import bcrypt
import jwt
import structlog
from fastapi import Response
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import TokenResponse, UserCreate
from app.config import settings
from app.shared.errors import AuthError, ValidationError

type TokenPayload = dict[str, object]

logger = structlog.get_logger()

_AUTH_REASON_ALIASES = {
    "Invalid email or password": "invalid_credentials",
    "User is inactive": "inactive_user",
    "Refresh token required": "refresh_token_required",
    "Invalid token": "invalid_token",
    "Invalid token type": "invalid_token_type",
    "Invalid refresh token": "invalid_refresh_token",
    "Token revoked": "token_revoked",
    "User not found or inactive": "user_not_found_or_inactive",
    "Current password is incorrect": "invalid_current_password",
    "New password must be different from current password": "password_reuse",
    "Email already registered": "email_already_registered",
}


def normalize_auth_reason(reason: object | None, *, fallback: str = "auth_error") -> str:
    if reason is None:
        return fallback

    raw_reason = getattr(reason, "detail", reason)
    text = str(raw_reason).strip()
    if not text:
        return fallback
    if text in _AUTH_REASON_ALIASES:
        return _AUTH_REASON_ALIASES[text]

    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return normalized or fallback


def _build_auth_log_fields(
    *,
    user: User | None = None,
    user_id: str | None = None,
    token_version: int | None = None,
    reason: str | None = None,
    auth_source: str | None = None,
    cleared_cookie_names: list[str] | None = None,
) -> dict[str, object]:
    fields: dict[str, object] = {}
    resolved_user_id = user_id or (str(user.id) if user is not None else None)
    if resolved_user_id is not None:
        fields["user_id"] = resolved_user_id
    resolved_token_version = token_version if token_version is not None else (
        get_token_version(user) if user is not None else None
    )
    if resolved_token_version is not None:
        fields["token_version"] = resolved_token_version
    if reason is not None:
        fields["reason"] = normalize_auth_reason(reason)
    if auth_source is not None:
        fields["auth_source"] = auth_source
    if cleared_cookie_names is not None:
        fields["cleared_cookie_names"] = cleared_cookie_names
    return fields


def log_auth_info(event: str, **kwargs: object) -> None:
    logger.info(event, audit_stream="auth", **kwargs)


def log_auth_warning(event: str, **kwargs: object) -> None:
    logger.warning(event, audit_stream="auth", **kwargs)


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


def create_csrf_token() -> str:
    return uuid.uuid4().hex


def decode_token_payload(token: str, expected_type: str | None = None) -> TokenPayload:
    try:
        payload = cast(
            TokenPayload,
            jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]),
        )
        token_type = payload.get("type")
        if expected_type is not None and token_type != expected_type:
            raise AuthError("Invalid token type")
        if not isinstance(payload.get("sub"), str):
            raise AuthError("Invalid token")
        return payload
    except InvalidTokenError:
        raise AuthError("Invalid token")


def decode_refresh_token(token: str) -> str:
    payload = decode_token_payload(token, expected_type="refresh")
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise AuthError("Invalid refresh token")
    return user_id


def set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    csrf_token = create_csrf_token()
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
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookies(
    response: Response,
    *,
    reason: str | None = None,
    user: User | None = None,
    user_id: str | None = None,
) -> None:
    cleared_cookie_names = [
        settings.access_cookie_name,
        settings.refresh_cookie_name,
        settings.csrf_cookie_name,
    ]
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
    log_auth_info(
        "auth_session_cleared",
        **_build_auth_log_fields(
            user=user,
            user_id=user_id,
            reason=reason,
            cleared_cookie_names=cleared_cookie_names,
        ),
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        log_auth_warning(
            "auth_register_failed",
            reason="email_already_registered",
            auth_source="registration",
        )
        raise ValidationError("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    log_auth_info(
        "auth_register_succeeded",
        user_id=str(user.id),
        auth_source="registration",
    )
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        log_auth_warning("auth_login_failed", reason="invalid_credentials")
        raise AuthError("Invalid email or password")
    if not user.is_active:
        log_auth_warning(
            "auth_login_failed",
            **_build_auth_log_fields(user=user, reason="inactive_user"),
        )
        raise AuthError("User is inactive")
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    if not verify_password(current_password, user.password_hash):
        log_auth_warning(
            "auth_password_change_failed",
            **_build_auth_log_fields(user=user, reason="invalid_current_password"),
        )
        raise AuthError("Current password is incorrect")
    if current_password == new_password:
        log_auth_warning(
            "auth_password_change_failed",
            **_build_auth_log_fields(user=user, reason="password_reuse"),
        )
        raise ValidationError("New password must be different from current password")
    user.password_hash = hash_password(new_password)
    user.token_version = get_token_version(user) + 1
    await db.commit()
    await db.refresh(user)
    log_auth_info("auth_password_changed", **_build_auth_log_fields(user=user))
    return user
