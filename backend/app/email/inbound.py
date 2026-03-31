from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from app.email.schemas import EmailWebhookPayload


@dataclass(frozen=True)
class InboundEmailMessage:
    sender: str
    from_address: str
    to_address: str
    subject: str
    text: str
    html: str
    source_provider: str = "webhook"
    source_message_id: str | None = None
    source_thread_id: str | None = None
    received_at: datetime | None = None

    @property
    def effective_sender(self) -> str:
        return self.sender or self.from_address

    @property
    def effective_body(self) -> str:
        return self.text or self.html

    @property
    def raw_body_hash(self) -> str:
        return hashlib.sha256(self.effective_body.encode()).hexdigest()

    @classmethod
    def from_webhook_payload(cls, payload: EmailWebhookPayload) -> "InboundEmailMessage":
        return cls(
            sender=payload.sender,
            from_address=payload.from_,
            to_address=payload.to,
            subject=payload.subject,
            text=payload.text,
            html=payload.html,
            source_provider="webhook",
        )
