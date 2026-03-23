"""Seed script: creates or updates a demo user/profile and optionally imports a resume.

Usage (from the backend directory):
    $env:JR_SEED_EMAIL = "seed.user@example.com"
    $env:JR_SEED_PASSWORD = "change-me-now"
    $env:JR_SEED_RESUME_PATH = "D:/path/to/resume.pdf"
    python seed_data.py
"""

from __future__ import annotations

import asyncio
import os
from decimal import Decimal
from pathlib import Path

SEED_EMAIL_ENV = "JR_SEED_EMAIL"
SEED_PASSWORD_ENV = "JR_SEED_PASSWORD"
SEED_RESUME_PATH_ENV = "JR_SEED_RESUME_PATH"

DEFAULT_SEED_EMAIL = "seed.user@example.com"
DEFAULT_DISPLAY_NAME = "JobRadar Seed User"
DEFAULT_RESUME_FILENAME = "seed_resume.pdf"


def _get_seed_email() -> str:
    return os.environ.get(SEED_EMAIL_ENV, DEFAULT_SEED_EMAIL).strip()


def _get_seed_password() -> str | None:
    password = os.environ.get(SEED_PASSWORD_ENV, "").strip()
    return password or None


def _get_resume_path() -> Path | None:
    configured_path = os.environ.get(SEED_RESUME_PATH_ENV, "").strip()
    if not configured_path:
        return None
    return Path(configured_path).expanduser().resolve()


def _load_resume_text(resume_path: Path) -> str:
    try:
        import fitz  # type: ignore[import-not-found]  # PyMuPDF
    except ImportError:
        return "(PDF uploaded; text extraction requires PyMuPDF)"

    doc = fitz.open(str(resume_path))
    try:
        return "".join(page.get_text() for page in doc)
    finally:
        doc.close()


async def main() -> None:
    # Setup imports lazily so the script can be discovered without booting the app.
    from sqlalchemy import select

    from app.auth.models import User
    from app.auth.service import hash_password
    from app.database import async_session_factory
    from app.profile.models import UserProfile
    from app.resume.models import ResumeVersion

    seed_email = _get_seed_email()
    seed_password = _get_seed_password()
    resume_path = _get_resume_path()

    async with async_session_factory() as db:
        existing = await db.scalar(select(User).where(User.email == seed_email))
        if existing:
            user = existing
            print(f"User already exists: {user.id}")
        else:
            if seed_password is None:
                raise RuntimeError(
                    f"Set {SEED_PASSWORD_ENV} before creating a new seed user.",
                )

            user = User(
                email=seed_email,
                password_hash=hash_password(seed_password),
                display_name=DEFAULT_DISPLAY_NAME,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            print(f"Created user: {user.id}")

        user_id = user.id

        profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        if profile is None:
            profile = UserProfile(user_id=user_id)
            db.add(profile)

        profile.full_name = DEFAULT_DISPLAY_NAME
        profile.email = seed_email
        profile.phone = "555-0100"
        profile.location = "Austin, TX, USA"

        profile.linkedin_url = "https://www.linkedin.com/in/example"
        profile.github_url = "https://github.com/example"
        profile.portfolio_url = "https://example.com/portfolio"

        profile.work_authorization = "OPT"
        profile.requires_sponsorship = True

        profile.current_title = "Machine Learning Engineer"
        profile.current_company = "Example Labs"
        profile.highest_degree = "MS Data Science"
        profile.graduation_year = 2025

        profile.city = "Austin"
        profile.state = "TX"
        profile.country = "USA"

        profile.education = [
            {
                "school": "Example University",
                "degree": "MS",
                "field": "Data Science",
                "start": "2023-08",
                "end": "2025-05",
            }
        ]

        profile.work_experience = [
            {
                "company": "Example Labs",
                "title": "Machine Learning Engineer",
                "start": "2025-06",
                "end": "Present",
                "description": "Building ML pipelines and deploying models at scale.",
            }
        ]

        profile.salary_min = Decimal("120000")
        profile.salary_max = Decimal("200000")

        profile.preferred_job_types = ["full-time"]
        profile.preferred_remote_types = ["remote", "hybrid", "onsite"]

        profile.search_queries = [
            "Machine Learning Engineer",
            "ML Engineer",
            "Data Scientist",
            "AI Engineer",
            "NLP Engineer",
            "Deep Learning Engineer",
            "MLOps Engineer",
            "Data Engineer",
        ]

        profile.search_locations = [
            "Remote",
            "Austin, TX",
            "New York, NY",
            "San Francisco, CA",
            "Texas",
            "USA",
        ]

        profile.watchlist_companies = [
            "Hugging Face",
            "Perplexity",
            "OpenAI",
            "Google",
            "Meta",
            "Uber",
            "Snap Inc",
            "Lyft",
            "Airbnb",
            "Microsoft",
            "Amazon",
        ]

        profile.answer_bank = {
            "Are you authorized to work in the US?": (
                "Yes, I am authorized to work in the US on OPT."
            ),
            "Will you now or in the future require visa sponsorship?": (
                "Yes, I will require H-1B visa sponsorship."
            ),
            "What is your desired salary?": "$120,000 - $200,000",
            "Are you willing to relocate?": "Yes, I am willing to relocate anywhere in the USA.",
            "How many years of experience do you have?": (
                "1 year of professional experience plus 2 years of academic "
                "project experience."
            ),
            "What is your highest level of education?": (
                "Master of Science in Data Science from Example University."
            ),
            "Are you over 18 years of age?": "Yes",
            "Do you have experience with Python?": (
                "Yes, Python is my primary programming language with 4+ years "
                "of experience."
            ),
            "Do you have experience with machine learning?": (
                "Yes, I have hands-on experience building and deploying ML "
                "models including NLP, computer vision, and recommendation "
                "systems."
            ),
        }

        profile.theme = "dark"
        profile.notifications_enabled = True
        profile.auto_apply_enabled = False

        print(f"Profile seeded for user {user_id}")

        if resume_path is None:
            print(f"No resume path configured; set {SEED_RESUME_PATH_ENV} to import a resume.")
        elif resume_path.exists():
            existing_resume = await db.scalar(
                select(ResumeVersion).where(ResumeVersion.user_id == user_id)
            )
            if existing_resume is None:
                resume_version = ResumeVersion(
                    user_id=user_id,
                    label="Main Resume",
                    filename=resume_path.name or DEFAULT_RESUME_FILENAME,
                    file_path=str(resume_path),
                    parsed_text=_load_resume_text(resume_path),
                    is_default=True,
                )
                db.add(resume_version)
                print(f"Resume uploaded: {resume_path.name}")
            else:
                print("Resume already exists, skipping")
        else:
            print(f"Resume file not found at {resume_path}")

        await db.commit()
        print("\nSeed complete.")
        print(f"  Email: {seed_email}")


if __name__ == "__main__":
    asyncio.run(main())
