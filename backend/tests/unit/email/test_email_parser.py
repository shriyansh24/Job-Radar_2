from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.email.parser import EmailParser
from app.email.schemas import EmailWebhookPayload
from app.email.service import EmailService
from app.jobs.models import Job
from app.pipeline.models import Application
from app.pipeline.schemas import ApplicationCreate, StatusTransition
from app.pipeline.service import PipelineService

# ---------------------------------------------------------------------------
# EmailParser unit tests (no DB)
# ---------------------------------------------------------------------------


class TestEmailParserRejection:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_rejection_unfortunately(self) -> None:
        result = self.parser.parse(
            sender="recruiting@acme.com",
            subject="Update on your application",
            body=(
                "Unfortunately, we will not be moving forward"
                " with your application at this time."
            ),
        )
        assert result is not None
        assert result.action == "rejection"
        assert result.confidence >= 0.80

    def test_rejection_position_filled(self) -> None:
        result = self.parser.parse(
            sender="noreply@greenhouse-mail.io",
            subject="Your application to Stripe",
            body="We appreciate your interest, however the position has been filled.",
        )
        assert result is not None
        assert result.action == "rejection"
        assert result.ats_source == "greenhouse"

    def test_rejection_decided_not_to_proceed(self) -> None:
        result = self.parser.parse(
            sender="talent@bigcorp.org",
            subject="Application Status Update",
            body="After careful review, we have decided not to proceed with your candidacy.",
        )
        assert result is not None
        assert result.action == "rejection"

    def test_rejection_other_candidates(self) -> None:
        result = self.parser.parse(
            sender="hr@startup.io",
            subject="Re: Software Engineer Application",
            body="We found other candidates who more closely match our needs at this time.",
        )
        assert result is not None
        assert result.action == "rejection"


class TestEmailParserInterview:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_interview_schedule(self) -> None:
        result = self.parser.parse(
            sender="recruiting@google.com",
            subject="Interview Invitation - Software Engineer",
            body=(
                "We would like to invite you to schedule an"
                " interview for the Software Engineer position."
            ),
        )
        assert result is not None
        assert result.action == "interview"

    def test_interview_phone_screen(self) -> None:
        result = self.parser.parse(
            sender="jobs@lever.co",
            subject="Next Steps: Phone Screen",
            body="We'd love to set up a phone screen with our hiring manager.",
        )
        assert result is not None
        assert result.action == "interview"
        assert result.ats_source == "lever"

    def test_interview_technical_assessment(self) -> None:
        result = self.parser.parse(
            sender="hiring@company.com",
            subject="Technical Assessment - Next Steps",
            body="As a next step, we'd like you to complete a technical assessment.",
        )
        assert result is not None
        assert result.action == "interview"

    def test_interview_onsite(self) -> None:
        result = self.parser.parse(
            sender="talent@meta.com",
            subject="On-Site Interview Confirmation",
            body="Your on-site interview is confirmed for March 28, 2026.",
        )
        assert result is not None
        assert result.action == "interview"


class TestEmailParserOffer:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_offer_pleased_to_offer(self) -> None:
        result = self.parser.parse(
            sender="hr@dreamco.com",
            subject="Offer of Employment",
            body="We are pleased to extend a formal offer for the Senior Engineer role.",
        )
        assert result is not None
        assert result.action == "offer"
        assert result.confidence >= 0.85

    def test_offer_compensation_package(self) -> None:
        result = self.parser.parse(
            sender="people@startup.com",
            subject="Your Compensation Package",
            body="Please review the attached compensation package details.",
        )
        assert result is not None
        assert result.action == "offer"

    def test_offer_letter(self) -> None:
        result = self.parser.parse(
            sender="recruiting@bigtech.com",
            subject="Offer Letter - Backend Engineer",
            body="Attached is your offer letter for the Backend Engineer position.",
        )
        assert result is not None
        assert result.action == "offer"


class TestEmailParserOutreach:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_outreach_found_profile(self) -> None:
        result = self.parser.parse(
            sender="recruiter@agency.com",
            subject="Exciting opportunity",
            body="I found your profile and think you'd be a great fit for a role at our client.",
        )
        assert result is not None
        assert result.action == "outreach"

    def test_outreach_would_you_be_interested(self) -> None:
        result = self.parser.parse(
            sender="jane@recruiting.io",
            subject="Senior Engineer Role",
            body="Would you be interested in exploring this exciting opportunity?",
        )
        assert result is not None
        assert result.action == "outreach"


class TestEmailParserNoSignal:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_unrelated_email(self) -> None:
        result = self.parser.parse(
            sender="newsletter@company.com",
            subject="Monthly Newsletter",
            body="Here are the latest updates from our team.",
        )
        assert result is None

    def test_empty_email(self) -> None:
        result = self.parser.parse(sender="", subject="", body="")
        assert result is None


class TestEmailParserCompanyExtraction:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_company_from_sender_domain(self) -> None:
        result = self.parser.parse(
            sender="hr@acme-corp.com",
            subject="Interview",
            body="We'd like to schedule an interview.",
        )
        assert result is not None
        assert result.company == "Acme Corp"

    def test_company_skips_ats_domain(self) -> None:
        result = self.parser.parse(
            sender="noreply@greenhouse-mail.io",
            subject="Application update",
            body="Unfortunately, we will not be moving forward.",
        )
        assert result is not None
        # Should not return "Greenhouse Mail" as the company
        assert result.company is None or "greenhouse" not in result.company.lower()

    def test_company_falls_back_to_body_when_sender_is_generic(self) -> None:
        result = self.parser.parse(
            sender="recruiting@gmail.com",
            subject="Interview Invitation",
            body="We would love to schedule an interview with you at Acme Labs.",
        )
        assert result is not None
        assert result.company == "Acme Labs"


class TestEmailParserATSDetection:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_greenhouse_detection(self) -> None:
        result = self.parser.parse(
            sender="no-reply@greenhouse-mail.io",
            subject="Your Application",
            body="Unfortunately, we won't be moving forward.",
        )
        assert result is not None
        assert result.ats_source == "greenhouse"

    def test_lever_detection(self) -> None:
        result = self.parser.parse(
            sender="notifications@lever.co",
            subject="Phone Screen",
            body="We'd like to schedule a phone screen.",
        )
        assert result is not None
        assert result.ats_source == "lever"

    def test_workday_detection(self) -> None:
        result = self.parser.parse(
            sender="jobs@myworkdayjobs.com",
            subject="Offer Letter",
            body="We are pleased to extend a formal offer.",
        )
        assert result is not None
        assert result.ats_source == "workday"

    def test_icims_detection(self) -> None:
        result = self.parser.parse(
            sender="noreply@icims.com",
            subject="Application Update",
            body="The position has been filled.",
        )
        assert result is not None
        assert result.ats_source == "icims"

    def test_ats_boosts_confidence(self) -> None:
        # Same email from ATS vs non-ATS should differ in confidence
        ats_result = self.parser.parse(
            sender="noreply@greenhouse-mail.io",
            subject="Rejection",
            body="Unfortunately, we will not be moving forward.",
        )
        plain_result = self.parser.parse(
            sender="hr@company.com",
            subject="Rejection",
            body="Unfortunately, we will not be moving forward.",
        )
        assert ats_result is not None
        assert plain_result is not None
        assert ats_result.confidence > plain_result.confidence


class TestEmailParserDateExtraction:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_extracts_iso_date(self) -> None:
        result = self.parser.parse(
            sender="hr@company.com",
            subject="Interview Scheduled",
            body="Your interview is scheduled for 2026-03-28.",
        )
        assert result is not None
        assert len(result.dates) == 1
        assert result.dates[0].month == 3
        assert result.dates[0].day == 28

    def test_extracts_written_date(self) -> None:
        result = self.parser.parse(
            sender="hr@company.com",
            subject="Interview Confirmation",
            body="Your on-site interview is on March 28, 2026.",
        )
        assert result is not None
        assert len(result.dates) >= 1

    def test_extracts_us_date(self) -> None:
        result = self.parser.parse(
            sender="hr@company.com",
            subject="Schedule your interview",
            body="Please confirm your availability for 3/28/2026.",
        )
        assert result is not None
        assert len(result.dates) == 1


class TestEmailParserJobTitle:
    def setup_method(self) -> None:
        self.parser = EmailParser()

    def test_extracts_title_from_position(self) -> None:
        result = self.parser.parse(
            sender="hr@company.com",
            subject="Update",
            body=(
                "Thank you for applying for the Senior Backend"
                " Engineer position. Unfortunately, we will"
                " not be moving forward."
            ),
        )
        assert result is not None
        assert result.job_title is not None
        assert "backend engineer" in result.job_title.lower()


# ---------------------------------------------------------------------------
# EmailService integration tests (with DB)
# ---------------------------------------------------------------------------


@pytest.fixture
async def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def sample_job(db_session: AsyncSession, user_id: uuid.UUID) -> Job:
    job = Job(
        id="email-test-job",
        user_id=user_id,
        source="test",
        title="Backend Engineer",
        company_name="Acme Corp",
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def applied_app(
    db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job
) -> Application:
    svc = PipelineService(db_session)
    app = await svc.create_application(
        ApplicationCreate(
            job_id=sample_job.id,
            company_name="Acme Corp",
            position_title="Backend Engineer",
            source="manual",
        ),
        user_id,
    )
    # Move to applied state
    app = await svc.transition_status(
        app.id,
        StatusTransition(new_status="applied", change_source="user"),
        user_id,
    )
    return app


@pytest.mark.asyncio
async def test_service_process_rejection(
    db_session: AsyncSession, user_id: uuid.UUID, applied_app: Application
) -> None:
    svc = EmailService(db_session)
    payload = EmailWebhookPayload(
        sender="recruiting@acme-corp.com",
        subject="Application Update",
        text="Unfortunately, we will not be moving forward with your application.",
    )
    result = await svc.process_webhook(payload, user_id)
    assert result.action == "rejection"
    assert result.application_id == applied_app.id
    assert result.status == "updated"


@pytest.mark.asyncio
async def test_service_process_interview(
    db_session: AsyncSession, user_id: uuid.UUID, applied_app: Application
) -> None:
    svc = EmailService(db_session)
    payload = EmailWebhookPayload(
        sender="recruiting@acme-corp.com",
        subject="Interview Invitation",
        text="We would like to schedule an interview with you.",
    )
    result = await svc.process_webhook(payload, user_id)
    assert result.action == "interview"
    assert result.application_id == applied_app.id
    assert result.status == "updated"


@pytest.mark.asyncio
async def test_service_no_signal(db_session: AsyncSession, user_id: uuid.UUID) -> None:
    svc = EmailService(db_session)
    payload = EmailWebhookPayload(
        sender="newsletter@company.com",
        subject="Weekly Update",
        text="Here are the latest news from our team.",
    )
    result = await svc.process_webhook(payload, user_id)
    assert result.status == "no_signal"


@pytest.mark.asyncio
async def test_service_no_matching_application(
    db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    svc = EmailService(db_session)
    payload = EmailWebhookPayload(
        sender="hr@unknown-company.com",
        subject="Application Status",
        body="",
        text="Unfortunately, we have decided not to proceed with your application.",
    )
    result = await svc.process_webhook(payload, user_id)
    assert result.action == "rejection"
    assert result.status == "no_match"


@pytest.mark.asyncio
async def test_service_creates_email_log(
    db_session: AsyncSession, user_id: uuid.UUID, applied_app: Application
) -> None:
    svc = EmailService(db_session)
    payload = EmailWebhookPayload(
        sender="recruiting@acme-corp.com",
        subject="Rejection Notice",
        text="Unfortunately, we will not be moving forward.",
    )
    await svc.process_webhook(payload, user_id)
    logs = await svc.list_logs(user_id)
    assert len(logs) == 1
    assert logs[0].parsed_action == "rejection"
    assert logs[0].sender == "recruiting@acme-corp.com"


@pytest.mark.asyncio
async def test_service_outreach_no_transition(
    db_session: AsyncSession, user_id: uuid.UUID, applied_app: Application
) -> None:
    """Outreach emails should not trigger a pipeline transition."""
    svc = EmailService(db_session)
    payload = EmailWebhookPayload(
        sender="recruiter@acme-corp.com",
        subject="Great opportunity",
        text="I found your profile and think you'd be a great fit.",
    )
    result = await svc.process_webhook(payload, user_id)
    assert result.action == "outreach"
    # Outreach has no status mapping, so it should not update
    assert result.status == "no_match"


@pytest.mark.asyncio
async def test_webhook_signature_verification() -> None:
    # Signature verification with wrong values should fail
    assert not EmailService.verify_webhook_signature("", "", "")
    assert not EmailService.verify_webhook_signature("ts", "tok", "bad")
