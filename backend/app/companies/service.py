from __future__ import annotations

import hashlib

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.companies.models import Company
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


class CompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_companies(self) -> list[Company]:
        result = await self.db.scalars(
            select(Company).order_by(Company.canonical_name)
        )
        return list(result.all())

    async def get_company(self, company_id: str) -> Company:
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        if company is None:
            raise NotFoundError(f"Company {company_id} not found")
        return company

    async def resolve_company(self, name: str) -> Company:
        result = await self.db.execute(
            select(Company).where(Company.canonical_name.ilike(name))
        )
        company = result.scalar_one_or_none()
        if company is not None:
            return company

        company_id = hashlib.sha256(name.lower().encode()).hexdigest()[:64]
        company = Company(id=company_id, canonical_name=name)
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        logger.info("company_created", company_id=company_id, name=name)
        return company
