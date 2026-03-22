from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_migration_module(module_name: str, filename: str):
    path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "migrations"
        / "versions"
        / filename
    )
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_002_downgrade_drops_pgvector_extension(monkeypatch):
    module = _load_migration_module("migration_002", "002_create_all_tables.py")
    calls: list[tuple[str, str]] = []

    fake_op = SimpleNamespace(
        get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
        drop_table=lambda name: calls.append(("drop_table", name)),
        execute=lambda sql: calls.append(("execute", sql)),
    )
    monkeypatch.setattr(module, "op", fake_op)

    module.downgrade()

    assert ("execute", "DROP EXTENSION IF EXISTS vector") in calls
