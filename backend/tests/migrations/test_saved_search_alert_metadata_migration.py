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


def test_saved_search_alert_metadata_migration_adds_columns(monkeypatch) -> None:
    module = _load_migration_module(
        "migration_20260330_saved_search_alerts",
        "20260330_add_saved_search_alert_metadata.py",
    )
    added_columns: list[tuple[str, str]] = []
    altered_columns: list[tuple[str, str]] = []

    def _add_column(table_name: str, column: sa.Column[object]) -> None:
        added_columns.append((table_name, column.name))

    def _alter_column(table_name: str, column_name: str, **_: object) -> None:
        altered_columns.append((table_name, column_name))

    fake_op = SimpleNamespace(add_column=_add_column, alter_column=_alter_column)
    monkeypatch.setattr(module, "op", fake_op)

    module.upgrade()

    assert ("saved_searches", "last_matched_at") in added_columns
    assert ("saved_searches", "last_match_count") in added_columns
    assert ("saved_searches", "last_error") in added_columns
    assert altered_columns == [("saved_searches", "last_match_count")]


def test_saved_search_alert_metadata_migration_downgrade_drops_columns(monkeypatch) -> None:
    module = _load_migration_module(
        "migration_20260330_saved_search_alerts_downgrade",
        "20260330_add_saved_search_alert_metadata.py",
    )
    dropped_columns: list[tuple[str, str]] = []

    def _drop_column(table_name: str, column_name: str) -> None:
        dropped_columns.append((table_name, column_name))

    fake_op = SimpleNamespace(drop_column=_drop_column)
    monkeypatch.setattr(module, "op", fake_op)

    module.downgrade()

    assert dropped_columns == [
        ("saved_searches", "last_error"),
        ("saved_searches", "last_match_count"),
        ("saved_searches", "last_matched_at"),
    ]
