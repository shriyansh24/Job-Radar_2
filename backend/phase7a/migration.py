"""Lightweight additive migration runner for Phase 7A.

No Alembic dependency. Migrations are registered as decorated async functions
and run in order. Already-applied migrations are skipped. The migration table
bootstraps itself on first run.

Usage by module branches:

    from backend.phase7a.migration import register_migration

    @register_migration("001_create_companies_table")
    async def migrate_001(conn):
        await conn.execute(text("CREATE TABLE IF NOT EXISTS companies (...)"))
"""

import logging
from datetime import datetime, timezone
from typing import Callable, Awaitable

from sqlalchemy import text

logger = logging.getLogger(__name__)

# Ordered registry of (name, async_fn) pairs.
# Module branches append to this by importing and using @register_migration.
_MIGRATIONS: list[tuple[str, Callable[..., Awaitable[None]]]] = []


def register_migration(name: str):
    """Decorator to register an additive migration function.

    Migrations are run in registration order. Names must be unique.
    The decorated function receives a SQLAlchemy async connection.

    Args:
        name: Unique migration identifier (e.g., "001_create_companies_table").
    """
    def decorator(fn: Callable[..., Awaitable[None]]):
        for existing_name, _ in _MIGRATIONS:
            if existing_name == name:
                raise ValueError(f"Duplicate migration name: {name}")
        _MIGRATIONS.append((name, fn))
        return fn
    return decorator


def get_registered_migrations() -> list[tuple[str, Callable[..., Awaitable[None]]]]:
    """Return a copy of the registered migration list (for testing)."""
    return list(_MIGRATIONS)


async def _ensure_migration_table(conn) -> None:
    """Create the migration tracking table if it doesn't exist."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS _phase7a_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL
        )
    """))


async def _get_applied_migrations(conn) -> set[str]:
    """Return set of already-applied migration names."""
    result = await conn.execute(
        text("SELECT name FROM _phase7a_migrations")
    )
    return {row[0] for row in result.fetchall()}


async def _record_migration(conn, name: str) -> None:
    """Record a migration as applied."""
    await conn.execute(
        text("INSERT INTO _phase7a_migrations (name, applied_at) VALUES (:name, :applied_at)"),
        {"name": name, "applied_at": datetime.now(timezone.utc).isoformat()},
    )


async def run_migrations(conn) -> list[str]:
    """Run all registered migrations that haven't been applied yet.

    Args:
        conn: SQLAlchemy async connection (inside a transaction).

    Returns:
        List of migration names that were applied in this run.
    """
    await _ensure_migration_table(conn)
    applied = await _get_applied_migrations(conn)
    newly_applied: list[str] = []

    for name, fn in _MIGRATIONS:
        if name in applied:
            logger.debug("Migration already applied: %s", name)
            continue

        logger.info("Applying migration: %s", name)
        try:
            await fn(conn)
            await _record_migration(conn, name)
            newly_applied.append(name)
            logger.info("Migration applied successfully: %s", name)
        except Exception:
            logger.exception("Migration failed: %s", name)
            raise

    if not newly_applied:
        logger.debug("No new migrations to apply.")
    else:
        logger.info("Applied %d migration(s): %s", len(newly_applied), newly_applied)

    return newly_applied
