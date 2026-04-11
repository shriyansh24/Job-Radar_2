import asyncio
from time import perf_counter

from sqlalchemy import Column, Integer, String, insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MockTarget(Base):
    __tablename__ = "mock_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


async def run_benchmark() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine)

    # Generate 10000 targets
    targets_for_loop = [MockTarget(name=f"Name {i}") for i in range(10000)]
    targets_for_add_all = [MockTarget(name=f"Name {i}") for i in range(10000)]
    targets_for_insert = [{"name": f"Name {i}"} for i in range(10000)]

    async with session_factory() as session:
        t = MockTarget(name="warmup")
        session.add(t)
        await session.commit()

    async with session_factory() as session:
        start_time = perf_counter()
        for t in targets_for_loop:
            session.add(t)
        loop_time = perf_counter() - start_time

        commit_start = perf_counter()
        await session.commit()
        loop_commit_time = perf_counter() - commit_start
        print(
            "db.add in loop:"
            f" add {loop_time:.4f}s + commit {loop_commit_time:.4f}s"
            f" = {loop_time + loop_commit_time:.4f}s"
        )

    async with session_factory() as session:
        start_time = perf_counter()
        session.add_all(targets_for_add_all)
        add_all_time = perf_counter() - start_time

        commit_start = perf_counter()
        await session.commit()
        add_all_commit_time = perf_counter() - commit_start
        print(
            "db.add_all:"
            f" add {add_all_time:.4f}s + commit {add_all_commit_time:.4f}s"
            f" = {add_all_time + add_all_commit_time:.4f}s"
        )

    async with session_factory() as session:
        start_time = perf_counter()
        await session.execute(insert(MockTarget), targets_for_insert)
        insert_time = perf_counter() - start_time

        commit_start = perf_counter()
        await session.commit()
        insert_commit_time = perf_counter() - commit_start
        print(
            "session.execute(insert):"
            f" execute {insert_time:.4f}s + commit {insert_commit_time:.4f}s"
            f" = {insert_time + insert_commit_time:.4f}s"
        )


if __name__ == "__main__":
    asyncio.run(run_benchmark())
