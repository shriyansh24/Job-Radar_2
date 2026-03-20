from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SavedSearchCreate(BaseModel):
    name: str
    filters: dict
    alert_enabled: bool = False


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    filters: dict
    alert_enabled: bool
    created_at: datetime


class AppSettingsResponse(BaseModel):
    theme: str = "dark"
    notifications_enabled: bool = True
    auto_apply_enabled: bool = False


class AppSettingsUpdate(BaseModel):
    theme: str | None = None
    notifications_enabled: bool | None = None
    auto_apply_enabled: bool | None = None
