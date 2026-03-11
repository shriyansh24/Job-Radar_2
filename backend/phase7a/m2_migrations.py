"""Module 2 — Search Expansion Engine: Additive migrations.

Migrations create the query_templates, expansion_rules, and query_performance
tables, seed default expansion rules, and create performance indexes.

All migrations are additive-only (no drops, no renames) per PHASE7A_LOCKED.md.
"""

import json
import logging

from sqlalchemy import text

from backend.phase7a.migration import register_migration
from backend.phase7a.m2_rules import get_all_default_rules

logger = logging.getLogger(__name__)


@register_migration("m2_001_create_query_templates_table")
async def m2_001_create_query_templates_table(conn) -> None:
    """Create the query_templates table for storing expanded query ASTs."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS query_templates (
            template_id TEXT(64) PRIMARY KEY,
            intent TEXT(255) NOT NULL UNIQUE,
            expansion_ast JSON NOT NULL,
            source_translations JSON,
            strictness TEXT(16) NOT NULL DEFAULT 'balanced',
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL,
            updated_at DATETIME
        )
    """))
    logger.info("Created query_templates table.")


@register_migration("m2_002_create_expansion_rules_table")
async def m2_002_create_expansion_rules_table(conn) -> None:
    """Create the expansion_rules table for deterministic expansion definitions."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expansion_rules (
            rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_type TEXT(32) NOT NULL,
            input_pattern TEXT(255) NOT NULL,
            output_variants JSON NOT NULL,
            priority INTEGER NOT NULL DEFAULT 100,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
    """))
    logger.info("Created expansion_rules table.")


@register_migration("m2_003_create_query_performance_table")
async def m2_003_create_query_performance_table(conn) -> None:
    """Create the query_performance table for per-source query metrics."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS query_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id TEXT(64) NOT NULL REFERENCES query_templates(template_id),
            source TEXT(32) NOT NULL,
            query_string TEXT NOT NULL,
            results_count INTEGER,
            new_jobs_count INTEGER,
            executed_at DATETIME NOT NULL,
            duration_ms INTEGER
        )
    """))
    logger.info("Created query_performance table.")


@register_migration("m2_004_create_query_performance_index")
async def m2_004_create_query_performance_index(conn) -> None:
    """Create the composite index on query_performance for fast lookups."""
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_query_performance_template_source
        ON query_performance (template_id, source, executed_at DESC)
    """))
    logger.info("Created idx_query_performance_template_source index.")


@register_migration("m2_005_seed_default_rules")
async def m2_005_seed_default_rules(conn) -> None:
    """Seed the expansion_rules table with default synonym, seniority, and skill rules.

    Only inserts rules that do not already exist (idempotent by input_pattern + rule_type).
    """
    default_rules = get_all_default_rules()
    inserted = 0

    for rule in default_rules:
        # Check if this rule already exists (idempotent)
        result = await conn.execute(
            text(
                "SELECT rule_id FROM expansion_rules "
                "WHERE rule_type = :rule_type AND input_pattern = :input_pattern"
            ),
            {"rule_type": rule.rule_type, "input_pattern": rule.input_pattern},
        )
        if result.fetchone() is not None:
            logger.debug(
                "Rule already exists: %s / %s", rule.rule_type, rule.input_pattern
            )
            continue

        await conn.execute(
            text(
                "INSERT INTO expansion_rules "
                "(rule_type, input_pattern, output_variants, priority, is_active) "
                "VALUES (:rule_type, :input_pattern, :output_variants, :priority, 1)"
            ),
            {
                "rule_type": rule.rule_type,
                "input_pattern": rule.input_pattern,
                "output_variants": json.dumps(rule.output_variants),
                "priority": rule.priority,
            },
        )
        inserted += 1

    logger.info("Seeded %d default expansion rules.", inserted)
