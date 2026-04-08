import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, Integer, String, Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    embedding = Column(String)

async def setup_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Insert 1000 jobs
        await conn.execute(
            text("INSERT INTO jobs (id, embedding) VALUES (:id, :emb)"),
            [{"id": i, "emb": "old"} for i in range(1000)]
        )
    return engine

async def run_n_plus_one(engine, updates):
    async with AsyncSession(engine) as db:
        start = time.perf_counter()
        for update in updates:
            await db.execute(
                text("UPDATE jobs SET embedding = :emb WHERE id = :id"),
                update,
            )
        await db.commit()
        return time.perf_counter() - start

async def run_executemany(engine, updates):
    async with AsyncSession(engine) as db:
        start = time.perf_counter()
        await db.execute(
            text("UPDATE jobs SET embedding = :emb WHERE id = :id"),
            updates,
        )
        await db.commit()
        return time.perf_counter() - start

async def main():
    engine = await setup_db()
    updates = [{"id": i, "emb": "new"} for i in range(1000)]

    # Warmup
    await run_n_plus_one(engine, updates[:10])

    t1 = await run_n_plus_one(engine, updates)
    print(f"N+1 approach: {t1:.4f} seconds")

    t2 = await run_executemany(engine, updates)
    print(f"Executemany approach: {t2:.4f} seconds")

    print(f"Improvement: {t1/t2:.2f}x faster")

if __name__ == "__main__":
    asyncio.run(main())
