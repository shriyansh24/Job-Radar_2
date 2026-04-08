"""Unit tests for VaultService using in-memory SQLite."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.models import CoverLetter
from app.resume.models import ResumeVersion
from app.shared.errors import NotFoundError
from app.vault.service import VaultService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_resume(
    db: AsyncSession, user_id: uuid.UUID, label: str = "My Resume"
) -> ResumeVersion:
    rv = ResumeVersion(user_id=user_id, label=label, parsed_text="Alice Smith, Engineer")
    db.add(rv)
    await db.commit()
    await db.refresh(rv)
    return rv


async def _make_cover_letter(
    db: AsyncSession, user_id: uuid.UUID, content: str = "Dear Hiring Manager"
) -> CoverLetter:
    cl = CoverLetter(user_id=user_id, style="professional", content=content)
    db.add(cl)
    await db.commit()
    await db.refresh(cl)
    return cl


# ---------------------------------------------------------------------------
# list_resumes
# ---------------------------------------------------------------------------


class TestListResumes:
    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, db_session: AsyncSession):
        svc = VaultService(db_session)
        result = await svc.list_resumes(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_only_own_resumes(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        r1 = await _make_resume(db_session, user_a, label="CV-A")
        await _make_resume(db_session, user_b, label="CV-B")

        svc = VaultService(db_session)
        result = await svc.list_resumes(user_a)
        assert len(result) == 1
        assert result[0].id == r1.id


# ---------------------------------------------------------------------------
# list_cover_letters
# ---------------------------------------------------------------------------


class TestListCoverLetters:
    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, db_session: AsyncSession):
        svc = VaultService(db_session)
        result = await svc.list_cover_letters(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_only_own_cover_letters(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        cl = await _make_cover_letter(db_session, user_a)
        await _make_cover_letter(db_session, user_b)

        svc = VaultService(db_session)
        result = await svc.list_cover_letters(user_a)
        assert len(result) == 1
        assert result[0].id == cl.id


# ---------------------------------------------------------------------------
# update_resume
# ---------------------------------------------------------------------------


class TestUpdateResume:
    @pytest.mark.asyncio
    async def test_updates_label(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        rv = await _make_resume(db_session, user_id, label="Old Label")
        svc = VaultService(db_session)

        updated = await svc.update_resume(rv.id, user_id, label="New Label")
        assert updated.label == "New Label"

    @pytest.mark.asyncio
    async def test_wrong_user_raises_not_found(self, db_session: AsyncSession):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        rv = await _make_resume(db_session, owner)
        svc = VaultService(db_session)

        with pytest.raises(NotFoundError):
            await svc.update_resume(rv.id, other, label="Hijack")

    @pytest.mark.asyncio
    async def test_missing_resume_raises_not_found(self, db_session: AsyncSession):
        svc = VaultService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_resume(uuid.uuid4(), uuid.uuid4(), label="X")


# ---------------------------------------------------------------------------
# update_cover_letter
# ---------------------------------------------------------------------------


class TestUpdateCoverLetter:
    @pytest.mark.asyncio
    async def test_updates_content(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        cl = await _make_cover_letter(db_session, user_id, content="Original")
        svc = VaultService(db_session)

        updated = await svc.update_cover_letter(cl.id, user_id, content="Updated content")
        assert updated.content == "Updated content"

    @pytest.mark.asyncio
    async def test_wrong_user_raises_not_found(self, db_session: AsyncSession):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        cl = await _make_cover_letter(db_session, owner)
        svc = VaultService(db_session)

        with pytest.raises(NotFoundError):
            await svc.update_cover_letter(cl.id, other, content="Hijack")

    @pytest.mark.asyncio
    async def test_missing_cover_letter_raises_not_found(self, db_session: AsyncSession):
        svc = VaultService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_cover_letter(uuid.uuid4(), uuid.uuid4(), content="X")


# ---------------------------------------------------------------------------
# delete_resume
# ---------------------------------------------------------------------------


class TestDeleteResume:
    @pytest.mark.asyncio
    async def test_deletes_own_resume(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        rv = await _make_resume(db_session, user_id)
        svc = VaultService(db_session)

        await svc.delete_resume(rv.id, user_id)
        result = await svc.list_resumes(user_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_wrong_user_raises_not_found(self, db_session: AsyncSession):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        rv = await _make_resume(db_session, owner)
        svc = VaultService(db_session)

        with pytest.raises(NotFoundError):
            await svc.delete_resume(rv.id, other)

    @pytest.mark.asyncio
    async def test_missing_resume_raises_not_found(self, db_session: AsyncSession):
        svc = VaultService(db_session)
        with pytest.raises(NotFoundError):
            await svc.delete_resume(uuid.uuid4(), uuid.uuid4())


# ---------------------------------------------------------------------------
# delete_cover_letter
# ---------------------------------------------------------------------------


class TestDeleteCoverLetter:
    @pytest.mark.asyncio
    async def test_deletes_own_cover_letter(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        cl = await _make_cover_letter(db_session, user_id)
        svc = VaultService(db_session)

        await svc.delete_cover_letter(cl.id, user_id)
        result = await svc.list_cover_letters(user_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_wrong_user_raises_not_found(self, db_session: AsyncSession):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        cl = await _make_cover_letter(db_session, owner)
        svc = VaultService(db_session)

        with pytest.raises(NotFoundError):
            await svc.delete_cover_letter(cl.id, other)

    @pytest.mark.asyncio
    async def test_missing_cover_letter_raises_not_found(self, db_session: AsyncSession):
        svc = VaultService(db_session)
        with pytest.raises(NotFoundError):
            await svc.delete_cover_letter(uuid.uuid4(), uuid.uuid4())
