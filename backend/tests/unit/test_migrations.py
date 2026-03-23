from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.database import Base

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = REPO_ROOT / "app" / "migrations" / "versions"


def _load_migration_module(module_name: str, filename: str):
    path = VERSIONS_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_pr14_revisions_are_linearized_to_one_head():
    config = Config(str(REPO_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["20260323_ml_model_artifacts"]


def test_pr14_revision_chain_links_every_migration():
    revisions = {
        "004": _load_migration_module("migration_004", "004_create_email_logs.py"),
        "20260323_networking": _load_migration_module(
            "migration_networking",
            "20260323_add_contacts_and_referral_requests.py",
        ),
        "20260323_archetypes": _load_migration_module(
            "migration_archetypes",
            "20260323_add_resume_archetypes.py",
        ),
        "20260323_create_dedup_feedback": _load_migration_module(
            "migration_dedup_feedback",
            "20260323_create_dedup_feedback.py",
        ),
        "20260323_form_learning": _load_migration_module(
            "migration_form_learning",
            "20260323_form_learning_tables.py",
        ),
        "20260323_ml_model_artifacts": _load_migration_module(
            "migration_ml_model_artifacts",
            "20260323_add_ml_model_artifacts.py",
        ),
    }
    expected_down_revisions = {
        "004": "20260321_db_audit_fixes",
        "20260323_networking": "004",
        "20260323_archetypes": "20260323_networking",
        "20260323_create_dedup_feedback": "20260323_archetypes",
        "20260323_form_learning": "20260323_create_dedup_feedback",
        "20260323_ml_model_artifacts": "20260323_form_learning",
    }

    for revision, expected_down_revision in expected_down_revisions.items():
        assert revisions[revision].down_revision == expected_down_revision


def test_ml_model_artifacts_upgrade_creates_expected_table_and_index(monkeypatch):
    module = _load_migration_module(
        "migration_ml_model_artifacts",
        "20260323_add_ml_model_artifacts.py",
    )
    calls: list[tuple[str, object]] = []

    fake_op = SimpleNamespace(
        create_table=lambda name, *columns, **kwargs: calls.append(
            ("create_table", name, columns, kwargs)
        ),
        create_index=lambda name, table_name, columns, **kwargs: calls.append(
            ("create_index", name, table_name, tuple(columns), kwargs)
        ),
    )
    monkeypatch.setattr(module, "op", fake_op)

    module.upgrade()

    table_call = next(call for call in calls if call[0] == "create_table")
    column_names = [
        column.name for column in table_call[2] if isinstance(column, sa.Column)
    ]

    assert table_call[1] == "ml_model_artifacts"
    assert column_names == [
        "id",
        "user_id",
        "model_name",
        "model_version",
        "model_bytes",
        "n_samples",
        "cv_accuracy",
        "positive_rate",
        "feature_names",
        "created_at",
    ]
    assert (
        "create_index",
        "ix_ml_model_artifacts_user_model",
        "ml_model_artifacts",
        ("user_id", "model_name"),
        {},
    ) in calls


def test_20260321_replace_fk_uses_default_constraint_name_offline(monkeypatch):
    module = _load_migration_module(
        "migration_20260321_db_audit_fixes",
        "20260321_db_audit_fixes.py",
    )
    calls: list[tuple[str, object]] = []

    fake_context = SimpleNamespace(is_offline_mode=lambda: True)
    fake_op = SimpleNamespace(
        drop_constraint=lambda name, table_name, type_: calls.append(
            ("drop_constraint", name, table_name, type_)
        ),
        create_foreign_key=(
            lambda name,
            source,
            referent,
            local_cols,
            remote_cols,
            ondelete=None: calls.append(
                (
                    "create_foreign_key",
                    name,
                    source,
                    referent,
                    tuple(local_cols),
                    tuple(remote_cols),
                    ondelete,
                )
            )
        ),
    )
    monkeypatch.setattr(module, "context", fake_context)
    monkeypatch.setattr(module, "op", fake_op)

    module._replace_fk("applications", ["job_id"], "jobs", ondelete="SET NULL")

    assert (
        "drop_constraint",
        "applications_job_id_fkey",
        "applications",
        "foreignkey",
    ) in calls
    assert (
        "create_foreign_key",
        "fk_applications_job_id_jobs",
        "applications",
        "jobs",
        ("job_id",),
        ("id",),
        "SET NULL",
    ) in calls


def test_test_metadata_includes_p2_tables():
    expected_tables = {
        "application_dedup",
        "contacts",
        "dedup_feedback",
        "email_logs",
        "field_mapping_rules",
        "ml_model_artifacts",
        "referral_requests",
        "resume_archetypes",
    }

    assert expected_tables.issubset(Base.metadata.tables)


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
