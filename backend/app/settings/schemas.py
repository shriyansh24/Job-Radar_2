from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

IntegrationProvider = Literal["openrouter", "serpapi", "theirstack", "apify", "google"]
IntegrationAuthType = Literal["api_key", "oauth"]
IntegrationConnectionStatus = Literal[
    "connected",
    "not_configured",
    "needs_reconnect",
    "sync_error",
]


class SavedSearchCreate(BaseModel):
    name: str
    filters: dict[str, Any]
    alert_enabled: bool = False


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    filters: dict[str, Any]
    alert_enabled: bool
    last_checked_at: datetime | None = None
    last_matched_at: datetime | None = None
    last_match_count: int = 0
    last_error: str | None = None
    created_at: datetime


class SavedSearchUpdate(BaseModel):
    name: str | None = None
    filters: dict[str, Any] | None = None
    alert_enabled: bool | None = None


class IntegrationUpsertRequest(BaseModel):
    api_key: str = Field(min_length=1)


class IntegrationResponse(BaseModel):
    provider: IntegrationProvider
    auth_type: IntegrationAuthType
    connected: bool
    status: IntegrationConnectionStatus
    masked_value: str | None = None
    account_email: str | None = None
    scopes: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    last_validated_at: datetime | None = None
    last_synced_at: datetime | None = None
    last_error: str | None = None


class GmailSyncResponse(BaseModel):
    provider: Literal["google"] = "google"
    messages_seen: int
    messages_processed: int
    duplicates_skipped: int
    signals_detected: int
    transitions_applied: int
    last_synced_at: datetime | None = None


class AppSettingsResponse(BaseModel):
    theme: str = "dark"
    notifications_enabled: bool = True
    auto_apply_enabled: bool = False


class AppSettingsUpdate(BaseModel):
    theme: str | None = None
    notifications_enabled: bool | None = None
    auto_apply_enabled: bool | None = None


class SavedSearchCheckResponse(BaseModel):
    search: SavedSearchResponse
    status: Literal["matched", "no_match"]
    new_matches: int
    notification_created: bool
    notification_id: uuid.UUID | None = None
    link: str
