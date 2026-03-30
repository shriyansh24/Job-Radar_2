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


def test_scrape_target_migration_creates_ats_identity_columns_and_index(monkeypatch) -> None:
    module = _load_migration_module(
        "migration_aaba1d3f957f",
        "aaba1d3f957f_create_scrape_targets_and_scrape_.py",
    )
    created_tables: dict[str, list[sa.Column[object]]] = {}
    created_indexes: list[tuple[str, str, list[str]]] = []

    def _create_table(name: str, *elements: object, **kwargs: object) -> None:
        created_tables[name] = [element for element in elements if isinstance(element, sa.Column)]

    def _create_index(name: str, table_name: str, columns: list[str], **kwargs: object) -> None:
        created_indexes.append((name, table_name, columns))

    fake_op = SimpleNamespace(
        create_table=_create_table,
        create_index=_create_index,
    )
    monkeypatch.setattr(module, "op", fake_op)

    module.upgrade()

    scrape_target_columns = {column.name for column in created_tables["scrape_targets"]}
    assert "ats_vendor" in scrape_target_columns
    assert "ats_board_token" in scrape_target_columns
    assert ("idx_targets_ats", "scrape_targets", ["ats_vendor"]) in created_indexes


def test_job_lifecycle_migration_links_jobs_back_to_scrape_targets(monkeypatch) -> None:
    module = _load_migration_module(
        "migration_45613a5a2f78",
        "45613a5a2f78_add_job_lifecycle_columns_and_tier_.py",
    )
    added_columns: list[tuple[str, str]] = []
    created_foreign_keys: list[tuple[str, str, str, list[str], list[str]]] = []

    def _add_column(table_name: str, column: sa.Column[object]) -> None:
        added_columns.append((table_name, column.name))

    def _create_foreign_key(
        name: str,
        source_table: str,
        referent_table: str,
        local_cols: list[str],
        remote_cols: list[str],
    ) -> None:
        created_foreign_keys.append((name, source_table, referent_table, local_cols, remote_cols))

    fake_op = SimpleNamespace(
        add_column=_add_column,
        create_foreign_key=_create_foreign_key,
    )
    monkeypatch.setattr(module, "op", fake_op)

    module.upgrade()

    assert ("jobs", "source_target_id") in added_columns
    assert (
        "fk_jobs_source_target_id",
        "jobs",
        "scrape_targets",
        ["source_target_id"],
        ["id"],
    ) in created_foreign_keys
