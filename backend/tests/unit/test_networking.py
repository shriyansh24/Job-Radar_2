from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.networking.schemas import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    OutreachRequest,
    ReferralRequestCreate,
    ReferralSuggestion,
)
from app.networking.service import NetworkingService


def _mock_contact(**overrides: object) -> SimpleNamespace:
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "name": "Alice Smith",
        "company": "Acme Corp",
        "role": "Engineering Manager",
        "relationship_strength": 4,
        "linkedin_url": "https://linkedin.com/in/alice",
        "email": "alice@acme.com",
        "last_contacted": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "notes": "Met at conference",
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_job(**overrides: object) -> SimpleNamespace:
    defaults = {
        "id": "job-abc123",
        "user_id": uuid.uuid4(),
        "title": "Software Engineer",
        "company_name": "Acme Corp",
        "location": "San Francisco",
        "summary_ai": "Build systems",
        "description_clean": "We need an engineer",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _build_service() -> tuple[NetworkingService, MagicMock]:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return NetworkingService(db), db


# ---------------------------------------------------------------------------
# Contact CRUD tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact():
    svc, db = _build_service()
    user_id = uuid.uuid4()

    async def fake_refresh(obj: object) -> None:
        pass

    db.refresh = AsyncMock(side_effect=fake_refresh)

    await svc.create_contact(
        ContactCreate(
            name="Bob Jones",
            company="TechCo",
            role="CTO",
            relationship_strength=5,
        ),
        user_id,
    )
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_contacts():
    svc, db = _build_service()
    user_id = uuid.uuid4()
    contacts = [_mock_contact(), _mock_contact(name="Bob")]

    result_mock = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = contacts
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    result = await svc.list_contacts(user_id)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_contact_found():
    svc, db = _build_service()
    contact = _mock_contact()
    db.scalar = AsyncMock(return_value=contact)

    result = await svc.get_contact(contact.id, contact.user_id)
    assert result.name == "Alice Smith"


@pytest.mark.asyncio
async def test_get_contact_not_found():
    svc, db = _build_service()
    db.scalar = AsyncMock(return_value=None)

    with pytest.raises(Exception) as exc_info:
        await svc.get_contact(uuid.uuid4(), uuid.uuid4())

    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_contact():
    svc, db = _build_service()
    contact = _mock_contact()
    db.scalar = AsyncMock(return_value=contact)

    await svc.update_contact(
        contact.id,
        ContactUpdate(role="VP Engineering"),
        contact.user_id,
    )
    assert contact.role == "VP Engineering"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_contact():
    svc, db = _build_service()
    contact = _mock_contact()
    db.scalar = AsyncMock(return_value=contact)

    await svc.delete_contact(contact.id, contact.user_id)
    db.delete.assert_awaited_once()
    db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Connection search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_find_connections():
    svc, db = _build_service()
    contacts = [_mock_contact(company="Acme Corp")]

    result_mock = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = contacts
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    result = await svc.find_connections(uuid.uuid4(), "Acme")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Referral suggestion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_suggest_referral_finds_contacts():
    svc, db = _build_service()
    user_id = uuid.uuid4()
    job = _mock_job(user_id=user_id)
    contact = _mock_contact(company="Acme Corp")

    db.scalar = AsyncMock(return_value=job)

    result_mock = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [contact]
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    suggestions = await svc.suggest_referral(user_id, "job-abc123")
    assert len(suggestions) == 1
    assert isinstance(suggestions[0], ReferralSuggestion)
    assert "Acme Corp" in suggestions[0].relevance_reason
    assert "jobs.user_id" in str(db.scalar.await_args_list[0].args[0])


@pytest.mark.asyncio
async def test_suggest_referral_job_not_found():
    svc, db = _build_service()
    db.scalar = AsyncMock(return_value=None)

    with pytest.raises(Exception) as exc_info:
        await svc.suggest_referral(uuid.uuid4(), "nonexistent")

    assert "not found" in str(exc_info.value.detail).lower()


# ---------------------------------------------------------------------------
# Outreach generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_outreach_success():
    svc, db = _build_service()
    contact = _mock_contact()
    job = _mock_job(user_id=contact.user_id)

    db.scalar = AsyncMock(side_effect=[contact, job])

    mock_router = MagicMock()
    mock_router.complete = AsyncMock(return_value="Hi Alice, I noticed a role at Acme...")
    mock_router._llm = MagicMock()
    mock_router._llm.close = AsyncMock()

    with patch("app.networking.service._build_router", return_value=mock_router):
        message = await svc.generate_outreach(contact.id, job.id, contact.user_id)

    assert "Alice" in message
    mock_router.complete.assert_awaited_once()
    assert "jobs.user_id" in str(db.scalar.await_args_list[1].args[0])


@pytest.mark.asyncio
async def test_generate_outreach_llm_failure():
    svc, db = _build_service()
    contact = _mock_contact()
    job = _mock_job(user_id=contact.user_id)

    db.scalar = AsyncMock(side_effect=[contact, job])

    mock_router = MagicMock()
    mock_router.complete = AsyncMock(side_effect=RuntimeError("LLM down"))
    mock_router._llm = MagicMock()
    mock_router._llm.close = AsyncMock()

    with patch("app.networking.service._build_router", return_value=mock_router):
        with pytest.raises(Exception) as exc_info:
            await svc.generate_outreach(contact.id, job.id, contact.user_id)

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_generate_outreach_contact_not_found():
    svc, db = _build_service()
    db.scalar = AsyncMock(return_value=None)

    with pytest.raises(Exception) as exc_info:
        await svc.generate_outreach(uuid.uuid4(), "job-123", uuid.uuid4())

    assert "not found" in str(exc_info.value.detail).lower()


# ---------------------------------------------------------------------------
# Referral request CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_referral_request():
    svc, db = _build_service()
    contact = _mock_contact()
    job = _mock_job(user_id=contact.user_id)
    user_id = contact.user_id

    # get_contact returns the contact; job lookup returns the user's job
    db.scalar = AsyncMock(side_effect=[contact, job])

    await svc.create_referral_request(
        ReferralRequestCreate(
            contact_id=contact.id,
            job_id="job-abc123",
            message_template="Hi, I'd love a referral...",
        ),
        user_id,
    )
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    assert "jobs.user_id" in str(db.scalar.await_args_list[1].args[0])


@pytest.mark.asyncio
async def test_create_referral_request_rejects_foreign_job():
    svc, db = _build_service()
    contact = _mock_contact()

    db.scalar = AsyncMock(side_effect=[contact, None])

    with pytest.raises(Exception) as exc_info:
        await svc.create_referral_request(
            ReferralRequestCreate(
                contact_id=contact.id,
                job_id="foreign-job",
                message_template="Hi, I'd love a referral...",
            ),
            contact.user_id,
        )

    assert "not found" in str(exc_info.value.detail).lower()
    assert "jobs.user_id" in str(db.scalar.await_args_list[1].args[0])


@pytest.mark.asyncio
async def test_list_referral_requests():
    svc, db = _build_service()

    rr = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        contact_id=uuid.uuid4(),
        job_id="job-123",
        status="draft",
        message_template="Hello",
        sent_at=None,
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )

    result_mock = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [rr]
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    result = await svc.list_referral_requests(rr.user_id)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_contact_response_schema():
    resp = ContactResponse(
        id=uuid.uuid4(),
        name="Test User",
        company="TestCo",
        relationship_strength=5,
    )
    assert resp.name == "Test User"
    assert resp.relationship_strength == 5


def test_referral_suggestion_schema():
    contact = ContactResponse(id=uuid.uuid4(), name="Test")
    suggestion = ReferralSuggestion(
        contact=contact,
        relevance_reason="Works at target company",
    )
    assert suggestion.suggested_message == ""
    assert "target company" in suggestion.relevance_reason


def test_outreach_request_schema():
    req = OutreachRequest(contact_id=uuid.uuid4(), job_id="job-123")
    assert req.job_id == "job-123"
