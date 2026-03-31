from __future__ import annotations

import hashlib
import hmac
import uuid
from typing import cast

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.email.inbound import InboundEmailMessage
from app.email.models import EmailLog
from app.email.parser import EmailParser, ParsedEmail
from app.email.schemas import EmailLogResponse, EmailWebhookPayload, EmailWebhookResponse
from app.notifications.service import NotificationService
from app.pipeline.models import Application
from app.pipeline.schemas import StatusTransition
from app.pipeline.service import PipelineService
from app.pipeline.state_machine import VALID_TRANSITIONS

logger = structlog.get_logger()

_ACTION_TO_STATUS: dict[str, str] = {
    "offer": "offer",
    "interview": "interviewing",
    "rejection": "rejected",
}


class EmailService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.parser = EmailParser()

    async def process_webhook(
        self, payload: EmailWebhookPayload, user_id: uuid.UUID
    ) -> EmailWebhookResponse:
        return await self.process_inbound_message(
            InboundEmailMessage.from_webhook_payload(payload),
            user_id,
        )

    async def process_inbound_message(
        self,
        message: InboundEmailMessage,
        user_id: uuid.UUID,
        *,
        auto_transition_min_confidence: float = 0.0,
    ) -> EmailWebhookResponse:
        body_hash = message.raw_body_hash
        duplicate = await self._find_duplicate_log(
            message,
            user_id=user_id,
            body_hash=body_hash,
        )
        if duplicate is not None:
            logger.info(
                "email_duplicate_skipped",
                user_id=str(user_id),
                source_provider=message.source_provider,
                source_message_id=message.source_message_id,
            )
            return EmailWebhookResponse(
                status="duplicate",
                action=duplicate.parsed_action,
                application_id=duplicate.matched_application_id,
                company=duplicate.company_extracted,
                confidence=duplicate.confidence,
                message="Inbound email was already processed.",
            )

        parsed = self.parser.parse(
            message.effective_sender,
            message.subject,
            message.effective_body,
        )

        if parsed is None:
            self.db.add(self._build_log(message, user_id=user_id, body_hash=body_hash))
            await self.db.commit()
            return EmailWebhookResponse(status="no_signal")

        application = await self._find_matching_application(parsed, user_id)
        self.db.add(
            self._build_log(
                message,
                user_id=user_id,
                body_hash=body_hash,
                parsed=parsed,
                matched_application_id=application.id if application else None,
            )
        )

        if application is None:
            await self.db.commit()
            return EmailWebhookResponse(
                status="no_match",
                action=parsed.action,
                company=parsed.company,
                confidence=parsed.confidence,
                message=(
                    f"Detected {parsed.action} from {parsed.company}"
                    " but no matching application found"
                ),
            )

        target_status = _ACTION_TO_STATUS.get(parsed.action)
        review_required = (
            target_status is not None and parsed.confidence < auto_transition_min_confidence
        )
        transitioned = False
        if (
            target_status
            and not review_required
            and self._can_transition(application.status, target_status)
        ):
            pipeline_svc = PipelineService(self.db)
            await pipeline_svc.transition_status(
                application.id,
                StatusTransition(
                    new_status=target_status,
                    change_source="email",
                    note=f"Auto-detected from email: {message.subject[:200]}",
                ),
                user_id,
            )
            transitioned = True

        action_label = parsed.action.replace("_", " ").title()
        notif_svc = NotificationService(self.db)
        await notif_svc.create(
            user_id=user_id,
            title=(
                f"Review email signal: {action_label} from {parsed.company or 'Unknown'}"
                if review_required
                else f"Email: {action_label} from {parsed.company or 'Unknown'}"
            ),
            body=(
                f"Subject: {message.subject[:200]} | Confidence {parsed.confidence:.2f}"
                if review_required
                else f"Subject: {message.subject[:200]}"
            ),
            notification_type="email_review" if review_required else "email",
            link="/email" if review_required else f"/applications/{application.id}",
        )

        await self.db.commit()

        status = (
            "review_required"
            if review_required
            else ("updated" if transitioned else "no_match")
        )
        return EmailWebhookResponse(
            status=status,
            action=parsed.action,
            application_id=application.id,
            company=parsed.company,
            confidence=parsed.confidence,
        )

    async def list_logs(
        self, user_id: uuid.UUID, *, limit: int = 50
    ) -> list[EmailLogResponse]:
        result = await self.db.scalars(
            select(EmailLog)
            .where(EmailLog.user_id == user_id)
            .order_by(EmailLog.created_at.desc())
            .limit(limit)
        )
        return [EmailLogResponse.model_validate(log) for log in result.all()]

    async def _find_duplicate_log(
        self,
        message: InboundEmailMessage,
        *,
        user_id: uuid.UUID,
        body_hash: str,
    ) -> EmailLog | None:
        if message.source_message_id:
            duplicate = await self.db.scalar(
                select(EmailLog).where(
                    EmailLog.user_id == user_id,
                    EmailLog.source_provider == message.source_provider,
                    EmailLog.source_message_id == message.source_message_id,
                )
            )
            if duplicate is not None:
                return duplicate
        return cast(
            EmailLog | None,
            await self.db.scalar(
            select(EmailLog).where(
                EmailLog.user_id == user_id,
                EmailLog.sender == message.effective_sender,
                EmailLog.subject == message.subject[:1000],
                EmailLog.raw_body_hash == body_hash,
            )
        )
        )

    def _build_log(
        self,
        message: InboundEmailMessage,
        *,
        user_id: uuid.UUID,
        body_hash: str,
        parsed: ParsedEmail | None = None,
        matched_application_id: uuid.UUID | None = None,
    ) -> EmailLog:
        return EmailLog(
            user_id=user_id,
            sender=message.effective_sender,
            subject=message.subject[:1000],
            parsed_action=parsed.action if parsed else None,
            confidence=parsed.confidence if parsed else None,
            matched_application_id=matched_application_id,
            source_provider=message.source_provider,
            source_message_id=message.source_message_id,
            source_thread_id=message.source_thread_id,
            source_received_at=message.received_at,
            company_extracted=parsed.company if parsed else None,
            job_title_extracted=parsed.job_title if parsed else None,
            raw_body_hash=body_hash,
        )

    async def _find_matching_application(
        self, parsed: ParsedEmail, user_id: uuid.UUID
    ) -> Application | None:
        if not parsed.company:
            return None

        company_lower = parsed.company.lower()
        result = await self.db.scalars(
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.updated_at.desc())
        )
        applications = result.all()

        for app in applications:
            if app.company_name and company_lower in app.company_name.lower():
                return app
            if app.company_name and app.company_name.lower() in company_lower:
                return app

        return None

    @staticmethod
    def _can_transition(current_status: str, target_status: str) -> bool:
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return target_status in allowed

    @staticmethod
    def verify_webhook_signature(
        timestamp: str, token: str, signature: str
    ) -> bool:
        if not settings.secret_key or not timestamp or not token or not signature:
            return False
        digest = hmac.new(
            settings.secret_key.encode(),
            f"{timestamp}{token}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(digest, signature)
