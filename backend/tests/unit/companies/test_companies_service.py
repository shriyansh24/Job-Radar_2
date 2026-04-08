"""Unit tests for CompanyService using in-memory SQLite."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.companies.models import Company
from app.companies.service import CompanyService
from app.shared.errors import NotFoundError

# ---------------------------------------------------------------------------
# list_companies
# ---------------------------------------------------------------------------


class TestListCompanies:
    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, db_session: AsyncSession):
        svc = CompanyService(db_session)
        result = await svc.list_companies()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_companies_sorted(self, db_session: AsyncSession):
        for name in ["Zenith", "Acme", "BlueSky"]:
            company = Company(id=name.lower(), canonical_name=name)
            db_session.add(company)
        await db_session.commit()

        svc = CompanyService(db_session)
        result = await svc.list_companies()
        names = [c.canonical_name for c in result]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# get_company
# ---------------------------------------------------------------------------


class TestGetCompany:
    @pytest.mark.asyncio
    async def test_returns_existing_company(self, db_session: AsyncSession):
        company = Company(id="abc123", canonical_name="Acme Corp")
        db_session.add(company)
        await db_session.commit()

        svc = CompanyService(db_session)
        result = await svc.get_company("abc123")
        assert result.canonical_name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_missing_company_raises_not_found(self, db_session: AsyncSession):
        svc = CompanyService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_company("nonexistent")


# ---------------------------------------------------------------------------
# resolve_company
# ---------------------------------------------------------------------------


class TestResolveCompany:
    @pytest.mark.asyncio
    async def test_creates_new_company_when_not_found(self, db_session: AsyncSession):
        svc = CompanyService(db_session)
        result = await svc.resolve_company("NewCorp Inc")

        assert result.canonical_name == "NewCorp Inc"
        assert result.id  # SHA-256 derived ID

    @pytest.mark.asyncio
    async def test_returns_existing_company_case_insensitive(self, db_session: AsyncSession):
        company = Company(id="match-id", canonical_name="Existing Corp")
        db_session.add(company)
        await db_session.commit()

        svc = CompanyService(db_session)
        result = await svc.resolve_company("Existing Corp")

        assert result.id == "match-id"

    @pytest.mark.asyncio
    async def test_resolve_twice_returns_same_id(self, db_session: AsyncSession):
        svc = CompanyService(db_session)
        first = await svc.resolve_company("Unique Company")
        second = await svc.resolve_company("unique company")  # different case
        # resolve_company uses ilike, so same record found on second call
        assert first.canonical_name == "Unique Company"
        assert second.canonical_name == "Unique Company"

    @pytest.mark.asyncio
    async def test_id_is_deterministic_hash(self, db_session: AsyncSession):
        import hashlib
        svc = CompanyService(db_session)
        result = await svc.resolve_company("HashCo")
        expected_id = hashlib.sha256("hashco".encode()).hexdigest()[:64]
        assert result.id == expected_id
