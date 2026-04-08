import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, insert

Base = declarative_base()

class MockTarget(Base):
    __tablename__ = 'mock_targets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

async def run_benchmark():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine)

    # Generate 10000 targets
    targets_for_loop = [MockTarget(name=f"Name {i}") for i in range(10000)]
    targets_for_add_all = [MockTarget(name=f"Name {i}") for i in range(10000)]
    targets_for_insert = [{"name": f"Name {i}"} for i in range(10000)]

    async with Session() as session:
        t = MockTarget(name="warmup")
        session.add(t)
        await session.commit()

    async with Session() as session:
        start_time = time.time()
        for t in targets_for_loop:
            session.add(t)
        loop_time = time.time() - start_time

        commit_start = time.time()
        await session.commit()
        loop_commit_time = time.time() - commit_start
        print(f"db.add in loop: add {loop_time:.4f}s + commit {loop_commit_time:.4f}s = {loop_time + loop_commit_time:.4f}s")

    async with Session() as session:
        start_time = time.time()
        session.add_all(targets_for_add_all)
        add_all_time = time.time() - start_time

        commit_start = time.time()
        await session.commit()
        add_all_commit_time = time.time() - commit_start
        print(f"db.add_all: add {add_all_time:.4f}s + commit {add_all_commit_time:.4f}s = {add_all_time + add_all_commit_time:.4f}s")

    async with Session() as session:
        start_time = time.time()
        await session.execute(insert(MockTarget), targets_for_insert)
        insert_time = time.time() - start_time

        commit_start = time.time()
        await session.commit()
        insert_commit_time = time.time() - commit_start
        print(f"session.execute(insert): execute {insert_time:.4f}s + commit {insert_commit_time:.4f}s = {insert_time + insert_commit_time:.4f}s")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
