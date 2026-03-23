from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_migration_module(module_name: str, filename: str):
    path = Path(__file__).resolve().parents[2] / "app" / "migrations" / "versions" / filename
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


def test_feature_revisions_form_a_single_linear_chain():
    add_ats = _load_migration_module(
        "migration_005", "005_add_ats_dedup_columns.py"
    )
    normalize = _load_migration_module(
        "migration_a2", "20260322_a2_normalization.py"
    )
    freshness = _load_migration_module(
        "migration_freshness", "20260322_add_freshness_score.py"
    )
    resume_ir = _load_migration_module(
        "migration_resume_ir", "20260322_add_resume_ir_columns.py"
    )

    assert add_ats.down_revision == "20260321_db_audit_fixes"
    assert normalize.down_revision == add_ats.revision
    assert freshness.down_revision == normalize.revision
    assert resume_ir.down_revision == freshness.revision
