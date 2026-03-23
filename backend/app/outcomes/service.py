from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.outcomes.models import ApplicationOutcome, CompanyInsight
from app.outcomes.schemas import (
    CompanyInsightResponse,
    OutcomeCreate,
    OutcomeUpdate,
    RejectionReasonCount,
    UserOutcomeStats,
)
from app.pipeline.models import Application
from app.shared.errors import NotFoundError, ValidationError


class OutcomeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_outcome(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID,
        data: OutcomeCreate,
    ) -> ApplicationOutcome:
        # Verify application exists and belongs to user
        result = await self.db.execute(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )
        application = result.scalar_one_or_none()
        if application is None:
            raise NotFoundError("Application not found")

        # Check if outcome already exists
        existing = await self.db.execute(
            select(ApplicationOutcome).where(
                ApplicationOutcome.application_id == application_id,
            )
        )
        outcome = existing.scalar_one_or_none()

        if outcome is not None:
            raise ValidationError(
                "Outcome already exists for this application. Use PATCH to update."
            )

        stage = data.stage_reached or application.status
        outcome = ApplicationOutcome(
            application_id=application_id,
            user_id=user_id,
            stage_reached=stage,
            rejection_reason=data.rejection_reason,
            rejection_stage=data.rejection_stage,
            days_to_response=data.days_to_response,
            offer_amount=data.offer_amount,
            offer_equity=data.offer_equity,
            offer_total_comp=data.offer_total_comp,
            negotiated_amount=data.negotiated_amount,
            final_decision=data.final_decision,
            was_ghosted=data.was_ghosted,
            referral_used=data.referral_used,
            cover_letter_used=data.cover_letter_used,
            application_method=data.application_method,
            feedback_notes=data.feedback_notes,
        )
        self.db.add(outcome)

        # Update company insight
        company_name = application.company_name
        if company_name:
            await self._update_company_insight(
                user_id=user_id,
                company_name=company_name,
                outcome=outcome,
            )

        await self.db.commit()
        await self.db.refresh(outcome)
        return outcome

    async def update_outcome(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID,
        data: OutcomeUpdate,
    ) -> ApplicationOutcome:
        result = await self.db.execute(
            select(ApplicationOutcome).where(
                ApplicationOutcome.application_id == application_id,
                ApplicationOutcome.user_id == user_id,
            )
        )
        outcome = result.scalar_one_or_none()
        if outcome is None:
            raise NotFoundError("Outcome not found for this application")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(outcome, field, value)

        await self.db.commit()
        await self.db.refresh(outcome)
        return outcome

    async def get_outcome(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ApplicationOutcome:
        result = await self.db.execute(
            select(ApplicationOutcome).where(
                ApplicationOutcome.application_id == application_id,
                ApplicationOutcome.user_id == user_id,
            )
        )
        outcome = result.scalar_one_or_none()
        if outcome is None:
            raise NotFoundError("Outcome not found")
        return outcome

    async def get_user_stats(self, user_id: uuid.UUID) -> UserOutcomeStats:
        # Total applications
        app_count_result = await self.db.execute(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )
        total_applications = app_count_result.scalar() or 0

        # Total outcomes
        outcome_count_result = await self.db.execute(
            select(func.count(ApplicationOutcome.id)).where(
                ApplicationOutcome.user_id == user_id
            )
        )
        total_outcomes = outcome_count_result.scalar() or 0

        # Average days to response
        avg_days_result = await self.db.execute(
            select(func.avg(ApplicationOutcome.days_to_response)).where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.days_to_response.isnot(None),
            )
        )
        avg_days = avg_days_result.scalar()
        avg_days_to_response = round(float(avg_days), 1) if avg_days is not None else None

        # Ghosting rate
        ghosted_count_result = await self.db.execute(
            select(func.count(ApplicationOutcome.id)).where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.was_ghosted.is_(True),
            )
        )
        ghosted_count = ghosted_count_result.scalar() or 0
        ghosting_rate = (
            round(ghosted_count / total_outcomes, 2) if total_outcomes > 0 else 0.0
        )

        # Response rate (outcomes with non-null days_to_response)
        responded_result = await self.db.execute(
            select(func.count(ApplicationOutcome.id)).where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.days_to_response.isnot(None),
            )
        )
        responded_count = responded_result.scalar() or 0
        response_rate = (
            round(responded_count / total_outcomes, 2) if total_outcomes > 0 else 0.0
        )

        # Offer rate
        offer_count_result = await self.db.execute(
            select(func.count(ApplicationOutcome.id)).where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.offer_amount.isnot(None),
            )
        )
        offer_count = offer_count_result.scalar() or 0
        offer_rate = (
            round(offer_count / total_outcomes, 2) if total_outcomes > 0 else 0.0
        )

        # Average offer amount
        avg_offer_result = await self.db.execute(
            select(func.avg(ApplicationOutcome.offer_amount)).where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.offer_amount.isnot(None),
            )
        )
        avg_offer = avg_offer_result.scalar()
        avg_offer_amount = round(float(avg_offer), 2) if avg_offer is not None else None

        # Top rejection reasons
        rejection_rows = await self.db.execute(
            select(
                ApplicationOutcome.rejection_reason,
                func.count(ApplicationOutcome.id).label("cnt"),
            )
            .where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.rejection_reason.isnot(None),
            )
            .group_by(ApplicationOutcome.rejection_reason)
            .order_by(func.count(ApplicationOutcome.id).desc())
            .limit(10)
        )
        top_rejection_reasons = [
            RejectionReasonCount(reason=row.rejection_reason, count=row.cnt)
            for row in rejection_rows
        ]

        # Stage distribution
        stage_rows = await self.db.execute(
            select(
                ApplicationOutcome.stage_reached,
                func.count(ApplicationOutcome.id).label("cnt"),
            )
            .where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.stage_reached.isnot(None),
            )
            .group_by(ApplicationOutcome.stage_reached)
        )
        stage_distribution = {row.stage_reached: row.cnt for row in stage_rows}

        return UserOutcomeStats(
            total_applications=total_applications,
            total_outcomes=total_outcomes,
            avg_days_to_response=avg_days_to_response,
            ghosting_rate=ghosting_rate,
            response_rate=response_rate,
            offer_rate=offer_rate,
            avg_offer_amount=avg_offer_amount,
            top_rejection_reasons=top_rejection_reasons,
            stage_distribution=stage_distribution,
        )

    async def get_company_insights(
        self,
        company_name: str,
        user_id: uuid.UUID,
    ) -> CompanyInsightResponse:
        result = await self.db.execute(
            select(CompanyInsight).where(
                CompanyInsight.company_name == company_name,
                CompanyInsight.user_id == user_id,
            )
        )
        insight = result.scalar_one_or_none()
        if insight is None:
            # Compute on the fly from outcomes
            return await self._compute_company_insight(company_name, user_id)
        return CompanyInsightResponse.model_validate(insight)

    async def _compute_company_insight(
        self,
        company_name: str,
        user_id: uuid.UUID,
    ) -> CompanyInsightResponse:
        """Compute company stats from outcomes when no cached insight exists."""
        # Get all outcomes for this company
        result = await self.db.execute(
            select(ApplicationOutcome)
            .join(Application, Application.id == ApplicationOutcome.application_id)
            .where(
                Application.company_name == company_name,
                ApplicationOutcome.user_id == user_id,
            )
        )
        outcomes = list(result.scalars().all())

        total = len(outcomes)
        if total == 0:
            raise NotFoundError(f"No outcome data found for company: {company_name}")

        ghosted = sum(1 for o in outcomes if o.was_ghosted)
        offers = [o for o in outcomes if o.offer_amount is not None]
        rejected = sum(1 for o in outcomes if o.rejection_reason is not None)
        responded = [o for o in outcomes if o.days_to_response is not None]

        avg_response = (
            sum(o.days_to_response for o in responded) / len(responded)
            if responded
            else None
        )
        avg_offer = (
            sum(o.offer_amount for o in offers) / len(offers) if offers else None
        )

        return CompanyInsightResponse(
            id=uuid.uuid4(),
            company_name=company_name,
            total_applications=total,
            callback_count=len(responded),
            avg_response_days=round(avg_response, 1) if avg_response is not None else None,
            ghosted_count=ghosted,
            ghost_rate=round(ghosted / total, 2) if total > 0 else 0.0,
            rejection_rate=round(rejected / total, 2) if total > 0 else 0.0,
            offer_rate=round(len(offers) / total, 2) if total > 0 else 0.0,
            offers_received=len(offers),
            avg_offer_amount=round(avg_offer, 2) if avg_offer is not None else None,
        )

    async def _update_company_insight(
        self,
        user_id: uuid.UUID,
        company_name: str,
        outcome: ApplicationOutcome,
    ) -> None:
        """Upsert company insight row with data from new outcome."""
        result = await self.db.execute(
            select(CompanyInsight).where(
                CompanyInsight.user_id == user_id,
                CompanyInsight.company_name == company_name,
            )
        )
        insight = result.scalar_one_or_none()

        if insight is None:
            insight = CompanyInsight(
                user_id=user_id,
                company_name=company_name,
                total_applications=0,
                callback_count=0,
                ghosted_count=0,
                offers_received=0,
            )
            self.db.add(insight)

        insight.total_applications += 1
        insight.last_applied_at = datetime.now(timezone.utc)

        if outcome.was_ghosted:
            insight.ghosted_count += 1

        if outcome.days_to_response is not None:
            insight.callback_count += 1
            # Running average
            if insight.avg_response_days is not None:
                total_days = insight.avg_response_days * (insight.callback_count - 1)
                insight.avg_response_days = (
                    total_days + outcome.days_to_response
                ) / insight.callback_count
            else:
                insight.avg_response_days = float(outcome.days_to_response)

        if outcome.offer_amount is not None:
            insight.offers_received += 1
            if insight.avg_offer_amount is not None:
                total_offer = insight.avg_offer_amount * (insight.offers_received - 1)
                insight.avg_offer_amount = (
                    total_offer + outcome.offer_amount
                ) / insight.offers_received
            else:
                insight.avg_offer_amount = float(outcome.offer_amount)

        # Recompute rates
        total = insight.total_applications
        if total > 0:
            insight.ghost_rate = round(insight.ghosted_count / total, 2)
            insight.offer_rate = round(insight.offers_received / total, 2)

        # Rejection rate needs a count of rejected outcomes for this company
        rejected_result = await self.db.execute(
            select(func.count(ApplicationOutcome.id))
            .join(Application, Application.id == ApplicationOutcome.application_id)
            .where(
                Application.company_name == company_name,
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.rejection_reason.isnot(None),
            )
        )
        rejected_count = rejected_result.scalar() or 0
        if total > 0:
            insight.rejection_rate = round(rejected_count / total, 2)
