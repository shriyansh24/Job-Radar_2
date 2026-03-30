from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import sqlalchemy as sa


def _load_migration_module(module_name: str, filename: str):
    path = Path(__file__).resolve().parents[2] / "app" / "migrations" / "versions" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_job_ats_identity_migration_adds_columns_and_indexes(monkeypatch) -> None:
    module = _load_migration_module(
        "migration_20260327_job_ats_identity",
        "20260327_add_job_ats_identity.py",
    )
    added_columns: list[tuple[str, str]] = []
    created_indexes: list[tuple[str, str, list[str], bool]] = []

    def _add_column(table_name: str, column: sa.Column[object]) -> None:
        added_columns.append((table_name, column.name))

    def _create_index(
        name: str,
        table_name: str,
        columns: list[str],
        *,
        unique: bool = False,
        **_: object,
    ) -> None:
        created_indexes.append((name, table_name, columns, unique))

    fake_op = SimpleNamespace(add_column=_add_column, create_index=_create_index)
    monkeypatch.setattr(module, "op", fake_op)

    module.upgrade()

    assert ("jobs", "ats_job_id") in added_columns
    assert ("jobs", "ats_provider") in added_columns
    assert ("jobs", "ats_composite_key") in added_columns
    assert ("idx_jobs_ats_job_id", "jobs", ["ats_job_id"], False) in created_indexes
    assert ("idx_jobs_ats_provider", "jobs", ["ats_provider"], False) in created_indexes
    assert ("uq_jobs_ats_composite_key", "jobs", ["ats_composite_key"], True) in created_indexes


def test_job_ats_identity_migration_downgrade_drops_indexes_and_columns(monkeypatch) -> None:
    module = _load_migration_module(
        "migration_20260327_job_ats_identity_downgrade",
        "20260327_add_job_ats_identity.py",
    )
    dropped_indexes: list[tuple[str, str]] = []
    dropped_columns: list[tuple[str, str]] = []

    def _drop_index(name: str, *, table_name: str) -> None:
        dropped_indexes.append((name, table_name))

    def _drop_column(table_name: str, column_name: str) -> None:
        dropped_columns.append((table_name, column_name))

    fake_op = SimpleNamespace(drop_index=_drop_index, drop_column=_drop_column)
    monkeypatch.setattr(module, "op", fake_op)

    module.downgrade()

    assert ("uq_jobs_ats_composite_key", "jobs") in dropped_indexes
    assert ("idx_jobs_ats_provider", "jobs") in dropped_indexes
    assert ("idx_jobs_ats_job_id", "jobs") in dropped_indexes
    assert ("jobs", "ats_composite_key") in dropped_columns
    assert ("jobs", "ats_provider") in dropped_columns
    assert ("jobs", "ats_job_id") in dropped_columns
