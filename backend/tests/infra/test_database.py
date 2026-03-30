from __future__ import annotations

from app.database import _engine_kwargs


def test_engine_kwargs_omit_pool_settings_for_sqlite():
    kwargs = _engine_kwargs("sqlite+aiosqlite:///:memory:")

    assert kwargs["echo"] is False
    assert "pool_size" not in kwargs
    assert "pool_pre_ping" not in kwargs


def test_engine_kwargs_include_pool_settings_for_postgres():
    kwargs = _engine_kwargs("postgresql+asyncpg://jobradar:jobradar@localhost/jobradar")

    assert kwargs["echo"] is False
    assert kwargs["pool_size"] == 20
    assert kwargs["max_overflow"] == 40
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_recycle"] == 3600
