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


def test_p2_tables_migration_upgrade_creates_tables_indexes_and_timezone_fix(
    monkeypatch,
) -> None:
    module = _load_migration_module("migration_005_upgrade", "005_create_p2_tables.py")
    created_tables: list[str] = []
    created_indexes: list[tuple[str, str, list[str], bool]] = []
    altered_columns: list[tuple[str, str]] = []

    def _create_table(name: str, *columns: sa.Column[object], **_: object) -> None:
        created_tables.append(name)

    def _create_index(
        name: str,
        table_name: str,
        columns: list[str],
        *,
        unique: bool = False,
        **_: object,
    ) -> None:
        created_indexes.append((name, table_name, columns, unique))

    def _alter_column(table_name: str, column_name: str, **_: object) -> None:
        altered_columns.append((table_name, column_name))

    fake_op = SimpleNamespace(
        create_table=_create_table,
        create_index=_create_index,
        alter_column=_alter_column,
    )
    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module, "_table_exists", lambda _name: False)

    module.upgrade()

    assert created_tables == [
        "resume_archetypes",
        "field_mapping_rules",
        "application_dedup",
        "dedup_feedback",
        "email_logs",
        "contacts",
        "referral_requests",
        "ml_model_artifacts",
        "application_outcomes",
        "company_insights",
    ]
    assert (
        "idx_dedup_feedback_pair",
        "dedup_feedback",
        ["job_a_id", "job_b_id"],
        False,
    ) in created_indexes
    assert ("idx_dedup_feedback_user", "dedup_feedback", ["user_id"], False) in (
        created_indexes
    )
    assert (
        "ix_ml_model_artifacts_user_model",
        "ml_model_artifacts",
        ["user_id", "model_name"],
        False,
    ) in created_indexes
    assert (
        "ix_application_outcomes_user_id",
        "application_outcomes",
        ["user_id"],
        False,
    ) in created_indexes
    assert (
        "ix_application_outcomes_application_id",
        "application_outcomes",
        ["application_id"],
        True,
    ) in created_indexes
    assert (
        "ix_company_insights_user_company",
        "company_insights",
        ["user_id", "company_name"],
        True,
    ) in created_indexes
    assert altered_columns == [("users", "created_at"), ("users", "updated_at")]


def test_p2_tables_migration_downgrade_drops_tables_and_restores_user_timestamps(
    monkeypatch,
) -> None:
    module = _load_migration_module("migration_005_downgrade", "005_create_p2_tables.py")
    dropped_tables: list[str] = []
    altered_columns: list[tuple[str, str]] = []

    def _drop_table(name: str) -> None:
        dropped_tables.append(name)

    def _alter_column(table_name: str, column_name: str, **_: object) -> None:
        altered_columns.append((table_name, column_name))

    fake_op = SimpleNamespace(drop_table=_drop_table, alter_column=_alter_column)
    monkeypatch.setattr(module, "op", fake_op)

    module.downgrade()

    assert altered_columns == [("users", "updated_at"), ("users", "created_at")]
    assert dropped_tables == [
        "company_insights",
        "application_outcomes",
        "ml_model_artifacts",
        "referral_requests",
        "contacts",
        "email_logs",
        "dedup_feedback",
        "application_dedup",
        "field_mapping_rules",
        "resume_archetypes",
    ]
