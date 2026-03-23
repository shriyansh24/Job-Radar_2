"""create all tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _is_pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _jsonb_col(name: str, *, nullable: bool = True, server_default: str | None = None):
    """Return a JSONB column on PostgreSQL, JSON on SQLite."""
    if _is_pg():
        col_type = sa.dialects.postgresql.JSONB
    else:
        col_type = sa.JSON
    kw: dict = {"nullable": nullable}
    if server_default is not None:
        kw["server_default"] = server_default
    return sa.Column(name, col_type(), **kw)


def _uuid_pk():
    """UUID primary key with gen_random_uuid() default on PostgreSQL."""
    return sa.Column(
        "id",
        sa.Uuid(),
        nullable=False,
        default=sa.text("gen_random_uuid()"),
    )


def _ts(name: str, *, nullable: bool = True, has_default: bool = True):
    """TIMESTAMPTZ column helper."""
    kw: dict = {"nullable": nullable}
    if has_default:
        kw["server_default"] = sa.func.now()
    return sa.Column(name, sa.DateTime(timezone=True), **kw)


def upgrade() -> None:
    is_pg = _is_pg()

    # Enable pgvector extension on PostgreSQL
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── jobs ─────────────────────────────────────────────────────────
    jobs_columns = [
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("company_name", sa.String(300), nullable=True),
        sa.Column("company_domain", sa.String(200), nullable=True),
        sa.Column("company_logo_url", sa.Text(), nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("location_city", sa.String(100), nullable=True),
        sa.Column("location_state", sa.String(100), nullable=True),
        sa.Column("location_country", sa.String(100), nullable=True),
        sa.Column("remote_type", sa.String(20), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=True),
        sa.Column("description_clean", sa.Text(), nullable=True),
        sa.Column("description_markdown", sa.Text(), nullable=True),
        sa.Column("salary_min", sa.Numeric(), nullable=True),
        sa.Column("salary_max", sa.Numeric(), nullable=True),
        sa.Column("salary_period", sa.String(20), nullable=True),
        sa.Column("salary_currency", sa.String(10), nullable=True, server_default="USD"),
        sa.Column("experience_level", sa.String(30), nullable=True),
        sa.Column("seniority_score", sa.Integer(), nullable=True),
        sa.Column("job_type", sa.String(30), nullable=True),
        _ts("posted_at", has_default=False),
        _ts("scraped_at"),
        _ts("expires_at", has_default=False),
        sa.Column("is_enriched", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        _ts("enriched_at", has_default=False),
        sa.Column("summary_ai", sa.Text(), nullable=True),
        _jsonb_col("skills_required", server_default=sa.text("'[]'"))
        if is_pg
        else sa.Column(
            "skills_required", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
        ),
        _jsonb_col("skills_nice_to_have", server_default=sa.text("'[]'"))
        if is_pg
        else sa.Column(
            "skills_nice_to_have", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
        ),
        _jsonb_col("tech_stack", server_default=sa.text("'[]'"))
        if is_pg
        else sa.Column("tech_stack", sa.JSON(), nullable=True, server_default=sa.text("'[]'")),
        _jsonb_col("red_flags", server_default=sa.text("'[]'"))
        if is_pg
        else sa.Column("red_flags", sa.JSON(), nullable=True, server_default=sa.text("'[]'")),
        _jsonb_col("green_flags", server_default=sa.text("'[]'"))
        if is_pg
        else sa.Column("green_flags", sa.JSON(), nullable=True, server_default=sa.text("'[]'")),
        sa.Column("match_score", sa.Numeric(5, 1), nullable=True),
        sa.Column("tfidf_score", sa.Numeric(5, 1), nullable=True),
        sa.Column("dedup_hash", sa.String(32), nullable=True),
        sa.Column("simhash", sa.BigInteger(), nullable=True),
        sa.Column("duplicate_of", sa.String(64), nullable=True),
        sa.Column("status", sa.String(20), nullable=True, server_default="new"),
        sa.Column("is_starred", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("is_hidden", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    ]

    # PostgreSQL-only columns: embedding (VECTOR) and search_vector (TSVECTOR)
    if is_pg:
        from pgvector.sqlalchemy import Vector

        jobs_columns.insert(-2, sa.Column("embedding", Vector(384), nullable=True))
        jobs_columns.insert(
            -2, sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR(), nullable=True)
        )

    op.create_table("jobs", *jobs_columns)

    # jobs indexes
    op.create_index("idx_jobs_user", "jobs", ["user_id"])
    op.create_index("idx_jobs_source", "jobs", ["source"])
    op.create_index("idx_jobs_scraped_at", "jobs", ["scraped_at"])
    op.create_index("idx_jobs_match_score", "jobs", ["match_score"])
    op.create_index("idx_jobs_dedup", "jobs", ["dedup_hash"])

    if is_pg:
        # GIN index on search_vector
        op.execute("CREATE INDEX idx_jobs_search ON jobs USING gin (search_vector)")
        # IVFFlat index on embedding
        op.execute(
            "CREATE INDEX idx_jobs_embedding ON jobs USING ivfflat (embedding vector_cosine_ops)"
        )

    # ── saved_searches ───────────────────────────────────────────────
    op.create_table(
        "saved_searches",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        _jsonb_col("filters", nullable=False)
        if is_pg
        else sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("alert_enabled", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # ── scraper_runs ─────────────────────────────────────────────────
    op.create_table(
        "scraper_runs",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=True, server_default="running"),
        sa.Column("jobs_found", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("jobs_new", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("jobs_updated", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        _ts("started_at"),
        _ts("completed_at", has_default=False),
        sa.Column("duration_seconds", sa.Numeric(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # ── career_pages ─────────────────────────────────────────────────
    op.create_table(
        "career_pages",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(300), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("use_spider", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("consecutive_failures", sa.Integer(), nullable=True, server_default="0"),
        _ts("last_scraped_at", has_default=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # ── user_profiles ────────────────────────────────────────────────
    user_profiles_cols = [
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True, unique=True),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("resume_filename", sa.String(200), nullable=True),
    ]
    if is_pg:
        user_profiles_cols.append(_jsonb_col("resume_parsed_structured"))
        user_profiles_cols.append(_jsonb_col("search_queries", server_default=sa.text("'[]'")))
        user_profiles_cols.append(_jsonb_col("search_locations", server_default=sa.text("'[]'")))
        user_profiles_cols.append(
            _jsonb_col("watchlist_companies", server_default=sa.text("'[]'"))
        )
    else:
        user_profiles_cols.append(sa.Column("resume_parsed_structured", sa.JSON(), nullable=True))
        user_profiles_cols.append(
            sa.Column("search_queries", sa.JSON(), nullable=True, server_default=sa.text("'[]'"))
        )
        user_profiles_cols.append(
            sa.Column("search_locations", sa.JSON(), nullable=True, server_default=sa.text("'[]'"))
        )
        user_profiles_cols.append(
            sa.Column(
                "watchlist_companies", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
            )
        )
    user_profiles_cols.extend(
        [
            sa.Column("linkedin_url", sa.Text(), nullable=True),
            sa.Column("github_url", sa.Text(), nullable=True),
            sa.Column("portfolio_url", sa.Text(), nullable=True),
        ]
    )
    if is_pg:
        user_profiles_cols.append(_jsonb_col("education", server_default=sa.text("'[]'")))
        user_profiles_cols.append(_jsonb_col("work_experience", server_default=sa.text("'[]'")))
    else:
        user_profiles_cols.append(
            sa.Column("education", sa.JSON(), nullable=True, server_default=sa.text("'[]'"))
        )
        user_profiles_cols.append(
            sa.Column("work_experience", sa.JSON(), nullable=True, server_default=sa.text("'[]'"))
        )
    user_profiles_cols.extend(
        [
            sa.Column("work_authorization", sa.String(100), nullable=True),
        ]
    )
    if is_pg:
        user_profiles_cols.append(
            _jsonb_col("preferred_job_types", server_default=sa.text("'[]'"))
        )
        user_profiles_cols.append(
            _jsonb_col("preferred_remote_types", server_default=sa.text("'[]'"))
        )
    else:
        user_profiles_cols.append(
            sa.Column(
                "preferred_job_types", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
            )
        )
        user_profiles_cols.append(
            sa.Column(
                "preferred_remote_types", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
            )
        )
    user_profiles_cols.extend(
        [
            sa.Column("salary_min", sa.Numeric(), nullable=True),
            sa.Column("salary_max", sa.Numeric(), nullable=True),
        ]
    )
    if is_pg:
        user_profiles_cols.append(_jsonb_col("answer_bank", server_default=sa.text("'{}'")))
    else:
        user_profiles_cols.append(
            sa.Column("answer_bank", sa.JSON(), nullable=True, server_default=sa.text("'{}'"))
        )
    user_profiles_cols.extend(
        [
            sa.Column("theme", sa.String(20), nullable=True, server_default="dark"),
            sa.Column(
                "notifications_enabled",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "auto_apply_enabled", sa.Boolean(), nullable=True, server_default=sa.text("false")
            ),
            _ts("created_at"),
            _ts("updated_at"),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        ]
    )

    op.create_table("user_profiles", *user_profiles_cols)

    # ── resume_versions ──────────────────────────────────────────────
    resume_versions_cols = [
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("filename", sa.String(200), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("parsed_text", sa.Text(), nullable=True),
    ]
    if is_pg:
        resume_versions_cols.append(_jsonb_col("parsed_structured"))
    else:
        resume_versions_cols.append(sa.Column("parsed_structured", sa.JSON(), nullable=True))
    resume_versions_cols.extend(
        [
            sa.Column("is_default", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            _ts("created_at"),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        ]
    )

    op.create_table("resume_versions", *resume_versions_cols)

    # ── applications ─────────────────────────────────────────────────
    op.create_table(
        "applications",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("company_name", sa.String(300), nullable=True),
        sa.Column("position_title", sa.String(500), nullable=True),
        sa.Column("status", sa.String(30), nullable=True, server_default="saved"),
        sa.Column("source", sa.String(50), nullable=True),
        _ts("applied_at", has_default=False),
        _ts("offer_at", has_default=False),
        _ts("rejected_at", has_default=False),
        _ts("follow_up_at", has_default=False),
        _ts("reminder_at", has_default=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("resume_version_id", sa.Uuid(), nullable=True),
        sa.Column("cover_letter_id", sa.Uuid(), nullable=True),
        sa.Column("salary_offered", sa.Numeric(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["resume_version_id"], ["resume_versions.id"]),
    )

    # ── application_status_history ───────────────────────────────────
    op.create_table(
        "application_status_history",
        _uuid_pk(),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("old_status", sa.String(30), nullable=True),
        sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("change_source", sa.String(50), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        _ts("changed_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
    )

    # ── auto_apply_profiles ──────────────────────────────────────────
    op.create_table(
        "auto_apply_profiles",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=True),
        sa.Column("github_url", sa.Text(), nullable=True),
        sa.Column("portfolio_url", sa.Text(), nullable=True),
        sa.Column("cover_letter_template", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # ── auto_apply_rules ─────────────────────────────────────────────
    auto_apply_rules_cols = [
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("min_match_score", sa.Numeric(), nullable=True),
    ]
    if is_pg:
        auto_apply_rules_cols.extend(
            [
                _jsonb_col("required_keywords", server_default=sa.text("'[]'")),
                _jsonb_col("excluded_keywords", server_default=sa.text("'[]'")),
                _jsonb_col("required_companies", server_default=sa.text("'[]'")),
                _jsonb_col("excluded_companies", server_default=sa.text("'[]'")),
                _jsonb_col("experience_levels", server_default=sa.text("'[]'")),
                _jsonb_col("remote_types", server_default=sa.text("'[]'")),
            ]
        )
    else:
        auto_apply_rules_cols.extend(
            [
                sa.Column(
                    "required_keywords", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
                sa.Column(
                    "excluded_keywords", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
                sa.Column(
                    "required_companies", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
                sa.Column(
                    "excluded_companies", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
                sa.Column(
                    "experience_levels", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
                sa.Column(
                    "remote_types", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
            ]
        )
    auto_apply_rules_cols.extend(
        [
            _ts("created_at"),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["profile_id"], ["auto_apply_profiles.id"]),
        ]
    )

    op.create_table("auto_apply_rules", *auto_apply_rules_cols)

    # ── auto_apply_runs ──────────────────────────────────────────────
    auto_apply_runs_cols = [
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("rule_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(30), nullable=True, server_default="pending"),
        sa.Column("ats_provider", sa.String(50), nullable=True),
    ]
    if is_pg:
        auto_apply_runs_cols.extend(
            [
                _jsonb_col("fields_filled", server_default=sa.text("'{}'")),
                _jsonb_col("fields_missed", server_default=sa.text("'[]'")),
                _jsonb_col("screenshots", server_default=sa.text("'[]'")),
            ]
        )
    else:
        auto_apply_runs_cols.extend(
            [
                sa.Column(
                    "fields_filled", sa.JSON(), nullable=True, server_default=sa.text("'{}'")
                ),
                sa.Column(
                    "fields_missed", sa.JSON(), nullable=True, server_default=sa.text("'[]'")
                ),
                sa.Column("screenshots", sa.JSON(), nullable=True, server_default=sa.text("'[]'")),
            ]
        )
    auto_apply_runs_cols.extend(
        [
            sa.Column("error_message", sa.Text(), nullable=True),
            _ts("started_at", has_default=False),
            _ts("completed_at", has_default=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
            sa.ForeignKeyConstraint(["rule_id"], ["auto_apply_rules.id"]),
        ]
    )

    op.create_table("auto_apply_runs", *auto_apply_runs_cols)

    # ── cover_letters ────────────────────────────────────────────────
    op.create_table(
        "cover_letters",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("style", sa.String(50), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
    )

    # ── interview_sessions ───────────────────────────────────────────
    interview_cols = [
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.String(64), nullable=True),
    ]
    if is_pg:
        interview_cols.extend(
            [
                _jsonb_col("questions", nullable=False),
                _jsonb_col("answers", server_default=sa.text("'[]'")),
                _jsonb_col("scores", server_default=sa.text("'[]'")),
            ]
        )
    else:
        interview_cols.extend(
            [
                sa.Column("questions", sa.JSON(), nullable=False),
                sa.Column("answers", sa.JSON(), nullable=True, server_default=sa.text("'[]'")),
                sa.Column("scores", sa.JSON(), nullable=True, server_default=sa.text("'[]'")),
            ]
        )
    interview_cols.extend(
        [
            sa.Column("overall_score", sa.Numeric(), nullable=True),
            _ts("created_at"),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        ]
    )

    op.create_table("interview_sessions", *interview_cols)

    # ── salary_cache ─────────────────────────────────────────────────
    salary_cache_cols = [
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("job_title", sa.String(500), nullable=True),
        sa.Column("company_name", sa.String(300), nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
    ]
    if is_pg:
        salary_cache_cols.append(_jsonb_col("market_data"))
    else:
        salary_cache_cols.append(sa.Column("market_data", sa.JSON(), nullable=True))
    salary_cache_cols.extend(
        [
            _ts("created_at"),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        ]
    )

    op.create_table("salary_cache", *salary_cache_cols)

    # ── companies ────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("canonical_name", sa.String(300), nullable=False),
        sa.Column("domain", sa.String(200), nullable=True),
        sa.Column("careers_url", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("ats_provider", sa.String(50), nullable=True),
        sa.Column("validation_state", sa.String(20), nullable=True, server_default="unverified"),
        sa.Column("confidence_score", sa.Numeric(), nullable=True, server_default="0"),
        sa.Column("job_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=True, server_default="0"),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── source_registry ──────────────────────────────────────────────
    op.create_table(
        "source_registry",
        _uuid_pk(),
        sa.Column("source_name", sa.String(50), nullable=False, unique=True),
        sa.Column("health_state", sa.String(20), nullable=True, server_default="unknown"),
        sa.Column("quality_score", sa.Numeric(), nullable=True, server_default="0"),
        sa.Column("total_jobs_found", sa.Integer(), nullable=True, server_default="0"),
        _ts("last_check_at", has_default=False),
        sa.Column("failure_count", sa.Integer(), nullable=True, server_default="0"),
        _ts("backoff_until", has_default=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── source_check_log ─────────────────────────────────────────────
    op.create_table(
        "source_check_log",
        _uuid_pk(),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("check_type", sa.String(30), nullable=True),
        sa.Column("check_status", sa.String(20), nullable=True),
        sa.Column("jobs_found", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        _ts("checked_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_id"], ["source_registry.id"]),
    )


def downgrade() -> None:
    is_pg = _is_pg()

    # Drop in reverse dependency order
    op.drop_table("source_check_log")
    op.drop_table("source_registry")
    op.drop_table("companies")
    op.drop_table("salary_cache")
    op.drop_table("interview_sessions")
    op.drop_table("cover_letters")
    op.drop_table("auto_apply_runs")
    op.drop_table("auto_apply_rules")
    op.drop_table("auto_apply_profiles")
    op.drop_table("application_status_history")
    op.drop_table("applications")
    op.drop_table("resume_versions")
    op.drop_table("user_profiles")
    op.drop_table("career_pages")
    op.drop_table("scraper_runs")
    op.drop_table("saved_searches")

    # Drop PostgreSQL-only indexes (created via raw SQL) before dropping jobs
    if is_pg:
        op.execute("DROP INDEX IF EXISTS idx_jobs_embedding")
        op.execute("DROP INDEX IF EXISTS idx_jobs_search")

    op.drop_table("jobs")
    if is_pg:
        op.execute("DROP EXTENSION IF EXISTS vector")
