from __future__ import annotations

import hashlib
import hmac
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.email.models import EmailLog
from app.email.parser import EmailParser, ParsedEmail
from app.email.schemas import EmailLogResponse, EmailWebhookPayload, EmailWebhookResponse
from app.notifications.service import NotificationService
from app.pipeline.models import Application
from app.pipeline.schemas import StatusTransition
from app.pipeline.service import PipelineService
from app.pipeline.state_machine import VALID_TRANSITIONS

logger = structlog.get_logger()

# Map parsed email action to pipeline status
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
        sender = payload.effective_sender
        body = payload.effective_body
        body_hash = hashlib.sha256(body.encode()).hexdigest()

        # Parse the email
        parsed = self.parser.parse(sender, payload.subject, body)

        if parsed is None:
            log = EmailLog(
                user_id=user_id,
                sender=sender,
                subject=payload.subject[:1000],
                parsed_action=None,
                raw_body_hash=body_hash,
            )
            self.db.add(log)
            await self.db.commit()
            return EmailWebhookResponse(status="no_signal")

        # Try to match to an existing application
        application = await self._find_matching_application(parsed, user_id)

        log = EmailLog(
            user_id=user_id,
            sender=sender,
            subject=payload.subject[:1000],
            parsed_action=parsed.action,
            confidence=parsed.confidence,
            matched_application_id=application.id if application else None,
            company_extracted=parsed.company,
            job_title_extracted=parsed.job_title,
            raw_body_hash=body_hash,
        )
        self.db.add(log)

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

        # Attempt pipeline transition
        target_status = _ACTION_TO_STATUS.get(parsed.action)
        transitioned = False
        if target_status and self._can_transition(application.status, target_status):
            pipeline_svc = PipelineService(self.db)
            await pipeline_svc.transition_status(
                application.id,
                StatusTransition(
                    new_status=target_status,
                    change_source="email",
                    note=f"Auto-detected from email: {payload.subject[:200]}",
                ),
                user_id,
            )
            transitioned = True

        # Create notification
        notif_svc = NotificationService(self.db)
        action_label = parsed.action.replace("_", " ").title()
        await notif_svc.create(
            user_id=user_id,
            title=f"Email: {action_label} from {parsed.company or 'Unknown'}",
            body=f"Subject: {payload.subject[:200]}",
            notification_type="email",
            link=f"/applications/{application.id}",
        )

        await self.db.commit()

        return EmailWebhookResponse(
            status="updated" if transitioned else "no_match",
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

    async def _find_matching_application(
        self, parsed: ParsedEmail, user_id: uuid.UUID
    ) -> Application | None:
        if not parsed.company:
            return None

        company_lower = parsed.company.lower()

        # Search for matching application by company name
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
