"""Seed script: Creates user account and populates profile for Shriyansh Singh.

Run from backend directory: python seed_data.py
"""

import asyncio
from pathlib import Path


async def main():
    # Setup Django-style imports
    from app.auth.models import User
    from app.auth.service import hash_password
    from app.database import async_session_factory
    from app.profile.models import UserProfile
    from app.resume.models import ResumeVersion

    async with async_session_factory() as db:
        from sqlalchemy import select

        # ── 1. Create User ──────────────────────────────────────────────
        existing = await db.scalar(select(User).where(User.email == "shriyansh.singh24@gmail.com"))
        if existing:
            user = existing
            print(f"User already exists: {user.id}")
        else:
            user = User(
                email="shriyansh.singh24@gmail.com",
                password_hash=hash_password("Shrisid@2407"),
                display_name="Shriyansh Singh",
                is_active=True,
            )
            db.add(user)
            await db.flush()
            print(f"Created user: {user.id}")

        user_id = user.id

        # ── 2. Create/Update Profile ────────────────────────────────────
        profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)

        # Personal
        profile.full_name = "Shriyansh Singh"
        profile.email = "shriyansh.singh24@gmail.com"
        profile.phone = "930-333-5141"
        profile.location = "Austin, TX, USA"

        # Links
        profile.linkedin_url = "https://www.linkedin.com/in/shriyansh-bir-singh/"
        profile.github_url = "https://github.com/shriyansh24"
        profile.portfolio_url = (
            "https://personalwebsite-9n7xiqgwk-shriyansh24s-projects.vercel.app/"
        )

        # Work Authorization
        profile.work_authorization = "OPT"
        profile.requires_sponsorship = True

        # Career
        profile.current_title = "Machine Learning Engineer"
        profile.current_company = "Apexon"
        profile.highest_degree = "MS Data Science"
        profile.graduation_year = 2025

        # Address
        profile.city = "Austin"
        profile.state = "TX"
        profile.country = "USA"

        # Education
        profile.education = [
            {
                "school": "Indiana University Bloomington",
                "degree": "MS",
                "field": "Data Science",
                "start": "2023-08",
                "end": "2025-05",
            }
        ]

        # Work Experience
        profile.work_experience = [
            {
                "company": "Apexon",
                "title": "Machine Learning Engineer",
                "start": "2025-06",
                "end": "Present",
                "description": "Building ML pipelines and deploying models at scale.",
            }
        ]

        # Salary
        from decimal import Decimal

        profile.salary_min = Decimal("120000")
        profile.salary_max = Decimal("200000")

        # Job Preferences
        profile.preferred_job_types = ["full-time"]
        profile.preferred_remote_types = ["remote", "hybrid", "onsite"]

        # Search Queries
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

        # Search Locations
        profile.search_locations = [
            "Remote",
            "Austin, TX",
            "New York, NY",
            "San Francisco, CA",
            "Texas",
            "USA",
        ]

        # Watchlist Companies
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
            "BNSF",
            "Amazon",
        ]

        # Answer Bank (common application questions)
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
                "Master of Science in Data Science from Indiana University "
                "Bloomington."
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

        # Theme
        profile.theme = "dark"
        profile.notifications_enabled = True
        profile.auto_apply_enabled = False

        print(f"Profile seeded for user {user_id}")

        # ── 3. Upload Resume ────────────────────────────────────────────
        resume_path = Path(r"C:\Users\shriy\Downloads\Shriyansh__Sing__Resume.pdf")
        if resume_path.exists():
            existing_resume = await db.scalar(
                select(ResumeVersion).where(ResumeVersion.user_id == user_id)
            )
            if not existing_resume:
                # Read and store resume text (basic extraction)
                # Try to extract text from PDF
                resume_text = ""
                try:
                    import fitz  # PyMuPDF

                    doc = fitz.open(str(resume_path))
                    for page in doc:
                        resume_text += page.get_text()
                    doc.close()
                except ImportError:
                    # Fallback: store raw bytes indicator
                    resume_text = "(PDF uploaded — text extraction requires PyMuPDF)"

                resume_version = ResumeVersion(
                    user_id=user_id,
                    label="Main Resume",
                    filename="Shriyansh__Sing__Resume.pdf",
                    file_path=str(resume_path),
                    parsed_text=resume_text,
                    is_default=True,
                )
                db.add(resume_version)
                print(f"Resume uploaded: {resume_path.name}")
            else:
                print("Resume already exists, skipping")
        else:
            print(f"Resume file not found at {resume_path}")

        # ── 4. Commit everything ────────────────────────────────────────
        await db.commit()
        print("\nSeed complete! You can now log in with:")
        print("  Email: shriyansh.singh24@gmail.com")
        print("  Password: Shrisid@2407")


if __name__ == "__main__":
    asyncio.run(main())
