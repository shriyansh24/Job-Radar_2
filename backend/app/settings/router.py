from __future__ import annotations

import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.integrations.google_oauth import GoogleOAuthError, normalize_return_to
from app.settings.schemas import (
    AppSettingsResponse,
    AppSettingsUpdate,
    GmailSyncResponse,
    IntegrationResponse,
    IntegrationUpsertRequest,
    SavedSearchCheckResponse,
    SavedSearchCreate,
    SavedSearchResponse,
    SavedSearchUpdate,
)
from app.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])
GOOGLE_CALLBACK_SUCCESS_CODE = "google_connected"
GOOGLE_CALLBACK_ERROR_CODE = "google_oauth_callback_failed"
GOOGLE_CALLBACK_DENIED_CODE = "google_oauth_denied"


@router.get("/searches", response_model=list[SavedSearchResponse])
async def list_saved_searches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedSearchResponse]:
    svc = SettingsService(db)
    items = await svc.list_saved_searches(user.id)
    return [SavedSearchResponse.model_validate(s) for s in items]


@router.post("/searches", response_model=SavedSearchResponse, status_code=201)
async def create_saved_search(
    data: SavedSearchCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    svc = SettingsService(db)
    s = await svc.create_saved_search(data, user.id)
    return SavedSearchResponse.model_validate(s)


@router.patch("/searches/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: uuid.UUID,
    data: SavedSearchUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    svc = SettingsService(db)
    search = await svc.update_saved_search(search_id, data, user.id)
    return SavedSearchResponse.model_validate(search)


@router.post("/searches/{search_id}/check", response_model=SavedSearchCheckResponse)
async def check_saved_search(
    search_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchCheckResponse:
    svc = SettingsService(db)
    result = await svc.check_saved_search(search_id, user.id)
    return SavedSearchCheckResponse(
        search=SavedSearchResponse.model_validate(result["search"]),
        status=result["status"],
        new_matches=result["new_matches"],
        notification_created=result["notification_created"],
        notification_id=result["notification_id"],
        link=result["link"],
    )


@router.delete("/searches/{search_id}", status_code=204, response_model=None)
async def delete_saved_search(
    search_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = SettingsService(db)
    await svc.delete_saved_search(search_id, user.id)


@router.get("/integrations", response_model=list[IntegrationResponse])
async def list_integrations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[IntegrationResponse]:
    svc = SettingsService(db)
    items = await svc.list_integrations(user.id)
    return [IntegrationResponse(**item) for item in items]


@router.get("/integrations/google/connect")
async def connect_google_integration(
    return_to: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    svc = SettingsService(db)
    url = svc.build_google_connect_url(user.id, return_to=return_to)
    return RedirectResponse(url=url, status_code=307)


@router.get("/integrations/google/callback")
async def google_integration_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    svc = SettingsService(db)
    if error:
        return RedirectResponse(
            url=_build_frontend_callback_url(
                return_to=None,
                status="error",
                provider="google",
                message=GOOGLE_CALLBACK_DENIED_CODE,
            ),
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(
            url=_build_frontend_callback_url(
                return_to=None,
                status="error",
                provider="google",
                message="missing_oauth_callback_params",
            ),
            status_code=302,
        )
    try:
        result = await svc.connect_google_integration(code=code, state_token=state)
    except GoogleOAuthError:
        return RedirectResponse(
            url=_build_frontend_callback_url(
                return_to=None,
                status="error",
                provider="google",
                message=GOOGLE_CALLBACK_ERROR_CODE,
            ),
            status_code=302,
        )
    return RedirectResponse(
        url=_build_frontend_callback_url(
            return_to=result["return_to"],
            status="connected",
            provider="google",
            message=GOOGLE_CALLBACK_SUCCESS_CODE,
        ),
        status_code=302,
    )


@router.post("/integrations/google/sync", response_model=GmailSyncResponse)
async def sync_google_integration(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GmailSyncResponse:
    svc = SettingsService(db)
    result = await svc.sync_google_integration(user.id)
    return GmailSyncResponse(**result)


@router.put("/integrations/{provider}", response_model=IntegrationResponse)
@router.patch("/integrations/{provider}", response_model=IntegrationResponse)
async def upsert_integration(
    provider: str,
    data: IntegrationUpsertRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IntegrationResponse:
    svc = SettingsService(db)
    integration = await svc.upsert_integration(provider, data.api_key, user.id)
    return IntegrationResponse(**integration)


@router.delete("/integrations/{provider}", status_code=204, response_model=None)
async def delete_integration(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = SettingsService(db)
    await svc.delete_integration(provider, user.id)


@router.get("/app", response_model=AppSettingsResponse)
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppSettingsResponse:
    svc = SettingsService(db)
    result = await svc.get_settings(user.id)
    return AppSettingsResponse(**result)


@router.patch("/app", response_model=AppSettingsResponse)
async def update_settings(
    data: AppSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppSettingsResponse:
    svc = SettingsService(db)
    result = await svc.update_settings(data, user.id)
    return AppSettingsResponse(**result)


def _build_frontend_callback_url(
    *,
    return_to: str | None,
    status: str,
    provider: str,
    message: str,
) -> str:
    from app.config import settings

    normalized_return_to = normalize_return_to(return_to)
    params = urlencode(
        {
            "integration_status": status,
            "integration_provider": provider,
            "integration_message": message,
        }
    )
    separator = "&" if "?" in normalized_return_to else "?"
    return (
        f"{settings.frontend_base_url.rstrip('/')}"
        f"{normalized_return_to}"
        f"{separator}{params}"
    )
