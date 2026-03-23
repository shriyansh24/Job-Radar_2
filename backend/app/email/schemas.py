from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailWebhookPayload(BaseModel):
    """Inbound email payload (SendGrid / Mailgun inbound parse format)."""

    sender: str = ""
    from_: str = ""
    to: str = ""
    subject: str = ""
    text: str = ""
    html: str = ""
    # Webhook signature verification
    timestamp: str = ""
    token: str = ""
    signature: str = ""

    @property
    def effective_sender(self) -> str:
        return self.sender or self.from_

    @property
    def effective_body(self) -> str:
        return self.text or self.html


class EmailWebhookResponse(BaseModel):
    status: str  # "updated", "no_match", "no_signal", "error"
    action: str | None = None
    application_id: uuid.UUID | None = None
    company: str | None = None
    confidence: float | None = None
    message: str | None = None


class EmailLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: str
    subject: str
    parsed_action: str | None = None
    confidence: float | None = None
    matched_application_id: uuid.UUID | None = None
    company_extracted: str | None = None
    job_title_extracted: str | None = None
    processed_at: datetime
    created_at: datetime
