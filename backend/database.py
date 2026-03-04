from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        await conn.run_sync(Base.metadata.create_all)

        # Enable WAL mode
        await conn.execute(
            __import__("sqlalchemy").text("PRAGMA journal_mode=WAL")
        )

        # Create FTS5 virtual table
        await conn.execute(__import__("sqlalchemy").text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
                job_id UNINDEXED,
                title,
                company_name,
                description_clean,
                skills_required,
                tech_stack,
                content='jobs',
                content_rowid='rowid'
            )
        """))

        # FTS triggers
        await conn.execute(__import__("sqlalchemy").text("""
            CREATE TRIGGER IF NOT EXISTS jobs_fts_insert AFTER INSERT ON jobs BEGIN
                INSERT INTO jobs_fts(job_id, title, company_name, description_clean, skills_required, tech_stack)
                VALUES (new.job_id, new.title, new.company_name, new.description_clean,
                        new.skills_required, new.tech_stack);
            END
        """))

        await conn.execute(__import__("sqlalchemy").text("""
            CREATE TRIGGER IF NOT EXISTS jobs_fts_update AFTER UPDATE ON jobs BEGIN
                DELETE FROM jobs_fts WHERE job_id = old.job_id;
                INSERT INTO jobs_fts(job_id, title, company_name, description_clean, skills_required, tech_stack)
                VALUES (new.job_id, new.title, new.company_name, new.description_clean,
                        new.skills_required, new.tech_stack);
            END
        """))

        await conn.execute(__import__("sqlalchemy").text("""
            CREATE TRIGGER IF NOT EXISTS jobs_fts_delete AFTER DELETE ON jobs BEGIN
                DELETE FROM jobs_fts WHERE job_id = old.job_id;
            END
        """))
