from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MLModelArtifact(Base):
    __tablename__ = "ml_model_artifacts"
    __table_args__ = (
        Index("ix_ml_model_artifacts_user_model", "user_id", "model_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[int] = mapped_column(Integer, default=1)
    model_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    n_samples: Mapped[int] = mapped_column(Integer, default=0)
    cv_accuracy: Mapped[float | None] = mapped_column(Float)
    positive_rate: Mapped[float | None] = mapped_column(Float)
    feature_names: Mapped[str | None] = mapped_column(
        String(1000)
    )  # comma-separated
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
