from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CopilotRequest(BaseModel):
    message: str
    context: dict | None = None
    job_id: str | None = None


class CoverLetterCreate(BaseModel):
    job_id: str
    style: str = "professional"
    template: str | None = None  # formal, startup, career-change, technical


class CoverLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: str | None = None
    style: str | None = None
    content: str
    created_at: datetime
