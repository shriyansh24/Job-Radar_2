from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    sender: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str] = mapped_column(String(1000), nullable=False)
    parsed_action: Mapped[str | None] = mapped_column(String(30))
    confidence: Mapped[float | None] = mapped_column()
    matched_application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True
    )
    source_provider: Mapped[str] = mapped_column(String(50), default="webhook", nullable=False)
    source_message_id: Mapped[str | None] = mapped_column(String(255))
    source_thread_id: Mapped[str | None] = mapped_column(String(255))
    source_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    company_extracted: Mapped[str | None] = mapped_column(String(300))
    job_title_extracted: Mapped[str | None] = mapped_column(String(500))
    raw_body_hash: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
