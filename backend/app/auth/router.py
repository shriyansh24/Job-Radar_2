from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.auth.service import (
    authenticate_user,
    clear_auth_cookies,
    create_tokens,
    decode_refresh_token,
    decode_token_payload,
    get_token_version,
    register_user,
    set_auth_cookies,
)
from app.config import settings
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await register_user(db, data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, data.email, data.password)
    tokens = create_tokens(str(user.id), token_version=get_token_version(user))
    set_auth_cookies(response, tokens)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    request: Request,
    data: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    import uuid as uuid_mod

    from sqlalchemy import select

    from app.shared.errors import AuthError

    refresh_token = data.refresh_token if data and data.refresh_token else None
    if not refresh_token:
        refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise AuthError("Refresh token required")
    payload = decode_token_payload(refresh_token, expected_type="refresh")
    user_id = decode_refresh_token(refresh_token)
    result = await db.execute(select(User).where(User.id == uuid_mod.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthError("User not found or inactive")
    if int(payload.get("ver", 0)) != get_token_version(user):
        raise AuthError("Token revoked")
    tokens = create_tokens(str(user.id), token_version=get_token_version(user))
    set_auth_cookies(response, tokens)
    return tokens


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if hasattr(current_user, "token_version"):
        current_user.token_version = get_token_version(current_user) + 1
        await db.commit()
        await db.refresh(current_user)
    clear_auth_cookies(response)
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
