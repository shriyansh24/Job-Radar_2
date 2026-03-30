from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.auth.models import User
from app.auto_apply.models import AutoApplyProfile
from app.workers.auto_apply_worker import run_auto_apply_batch


@pytest.mark.asyncio
async def test_worker_skips_when_disabled(monkeypatch):
    class FakeSettings:
        auto_apply_enabled = False

    monkeypatch.setattr("app.workers.auto_apply_worker.Settings", lambda: FakeSettings())

    await run_auto_apply_batch({})


@pytest.mark.asyncio
async def test_worker_runs_all_active_profile_users(db_session, monkeypatch):
    user_one = User(email="worker1@example.com", password_hash="pw")
    user_two = User(email="worker2@example.com", password_hash="pw")
    db_session.add_all([user_one, user_two])
    await db_session.flush()

    db_session.add_all(
        [
            AutoApplyProfile(user_id=user_one.id, name="One", is_active=True),
            AutoApplyProfile(user_id=user_two.id, name="Two", is_active=True),
        ]
    )
    await db_session.commit()

    class FakeSettings:
        auto_apply_enabled = True
        openrouter_api_key = ""
        default_llm_model = "test-model"

    @asynccontextmanager
    async def fake_session_factory():
        yield db_session

    calls: list = []

    class FakeOrchestrator:
        def __init__(self, db, settings, llm_client):  # noqa: ANN001
            self.db = db
            self.settings = settings
            self.llm_client = llm_client

        async def run_batch(self, user_id):
            calls.append(user_id)
            return [SimpleNamespace(id="run")]

    monkeypatch.setattr("app.workers.auto_apply_worker.Settings", lambda: FakeSettings())
    monkeypatch.setattr("app.workers.auto_apply_worker.LLMClient", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.workers.auto_apply_worker.async_session_factory",
        fake_session_factory,
    )
    monkeypatch.setattr("app.workers.auto_apply_worker.AutoApplyOrchestrator", FakeOrchestrator)

    await run_auto_apply_batch({})

    assert set(calls) == {user_one.id, user_two.id}
