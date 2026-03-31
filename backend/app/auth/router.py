from __future__ import annotations

import uuid as uuid_mod

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.service import AdminService
from app.auth.models import User
from app.auth.schemas import (
    AuthSessionResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    UserCreate,
    UserResponse,
)
from app.auth.service import (
    authenticate_user,
    change_password,
    clear_auth_cookies,
    create_session_response,
    create_tokens,
    decode_refresh_token,
    decode_token_payload,
    get_token_version,
    log_auth_info,
    log_auth_warning,
    normalize_auth_reason,
    register_user,
    set_auth_cookies,
)
from app.config import settings
from app.dependencies import get_current_user, get_db
from app.shared.audit_sink import publish_auth_audit_event
from app.shared.errors import AuthError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await register_user(db, data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=AuthSessionResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    user = await authenticate_user(db, data.email, data.password)
    tokens = create_tokens(str(user.id), token_version=get_token_version(user))
    set_auth_cookies(response, tokens)
    log_auth_info(
        "auth_login_succeeded",
        user_id=str(user.id),
        token_version=get_token_version(user),
        auth_source="password",
    )
    await publish_auth_audit_event(
        "auth_login_succeeded",
        user_id=str(user.id),
        token_version=get_token_version(user),
        auth_source="password",
    )
    return create_session_response()


@router.post("/refresh", response_model=AuthSessionResponse)
async def refresh(
    response: Response,
    request: Request,
    data: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    refresh_token = data.refresh_token if data and data.refresh_token else None
    auth_source = "body" if refresh_token else "cookie"
    refresh_user_id: str | None = None
    if not refresh_token:
        refresh_token = request.cookies.get(settings.refresh_cookie_name)
    try:
        if not refresh_token:
            raise AuthError("Refresh token required")
        payload = decode_token_payload(refresh_token, expected_type="refresh")
        refresh_user_id = decode_refresh_token(refresh_token)
        result = await db.execute(select(User).where(User.id == uuid_mod.UUID(refresh_user_id)))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise AuthError("User not found or inactive")
        token_version_value = payload.get("ver", 0)
        if not isinstance(token_version_value, int):
            if isinstance(token_version_value, str) and token_version_value.isdigit():
                token_version = int(token_version_value)
            else:
                raise AuthError("Token revoked")
        else:
            token_version = token_version_value
        if token_version != get_token_version(user):
            raise AuthError("Token revoked")
    except AuthError as exc:
        log_auth_warning(
            "auth_refresh_failed",
            user_id=refresh_user_id,
            reason=normalize_auth_reason(exc),
            auth_source=auth_source,
        )
        await publish_auth_audit_event(
            "auth_refresh_failed",
            user_id=refresh_user_id,
            reason=normalize_auth_reason(exc),
            auth_source=auth_source,
        )
        raise

    tokens = create_tokens(str(user.id), token_version=get_token_version(user))
    set_auth_cookies(response, tokens)
    log_auth_info(
        "auth_refresh_succeeded",
        user_id=str(user.id),
        token_version=get_token_version(user),
        auth_source=auth_source,
    )
    await publish_auth_audit_event(
        "auth_refresh_succeeded",
        user_id=str(user.id),
        token_version=get_token_version(user),
        auth_source=auth_source,
    )
    return create_session_response()


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result: dict[str, str]
    if hasattr(current_user, "token_version"):
        current_user.token_version = get_token_version(current_user) + 1
        await db.commit()
        await db.refresh(current_user)
    log_auth_info(
        "auth_logout_succeeded",
        user_id=str(current_user.id),
        token_version=get_token_version(current_user),
    )
    clear_auth_cookies(response, reason="logout", user=current_user)
    await publish_auth_audit_event(
        "auth_logout_succeeded",
        user_id=str(current_user.id),
        token_version=get_token_version(current_user),
        auth_source="cookie",
    )
    result = {"status": "ok"}
    return result


@router.post("/change-password", response_model=AuthSessionResponse)
async def change_password_route(
    data: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    user = await change_password(db, current_user, data.current_password, data.new_password)
    tokens = create_tokens(str(user.id), token_version=get_token_version(user))
    set_auth_cookies(response, tokens)
    return create_session_response()


@router.delete("/account", status_code=204, response_model=None)
async def delete_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    user_id = str(current_user.id)
    admin_service = AdminService(db)
    await admin_service.clear_data(current_user.id, commit=False)
    await db.delete(current_user)
    await db.commit()
    log_auth_info("auth_account_deleted", user_id=user_id)
    clear_auth_cookies(response, reason="account_deleted", user_id=user_id)
    await publish_auth_audit_event("auth_account_deleted", user_id=user_id)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
