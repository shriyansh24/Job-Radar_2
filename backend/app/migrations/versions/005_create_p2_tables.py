"""Create all P2 feature tables and fix users timestamp columns.

Revision ID: 005
Revises: 7021f28ab5e0
Create Date: 2026-03-23

Consolidation migration: the individual branch migrations (004,
20260323_networking, 20260323_archetypes, 20260323_create_dedup_feedback,
20260323_form_learning) were stamped but never executed against the live DB.
This single migration creates all 10 missing tables idempotently.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "7021f28ab5e0"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    return sa.inspect(conn).has_table(name)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # B5 - Resume Archetypes
    # ------------------------------------------------------------------
    if not _table_exists("resume_archetypes"):
        op.create_table(
            "resume_archetypes",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("target_role_type", sa.String(200), nullable=True),
            sa.Column("base_ir_json", sa.JSON(), nullable=True),
            sa.Column("emphasis_sections", sa.JSON(), nullable=True),
            sa.Column("keyword_priorities", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )

    # ------------------------------------------------------------------
    # C7 - Form Learning
    # ------------------------------------------------------------------
    if not _table_exists("field_mapping_rules"):
        op.create_table(
            "field_mapping_rules",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("ats_provider", sa.String(50), index=True),
            sa.Column("field_label_hash", sa.String(64), index=True),
            sa.Column("field_label", sa.Text(), nullable=False),
            sa.Column("semantic_key", sa.String(200), nullable=False),
            sa.Column("confidence", sa.Float(), default=0.8),
            sa.Column("source", sa.String(30), default="llm"),
            sa.Column("times_seen", sa.Integer(), default=1),
            sa.Column(
                "last_seen",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint(
                "ats_provider",
                "field_label_hash",
                name="uq_field_mapping_provider_hash",
            ),
        )

    if not _table_exists("application_dedup"):
        op.create_table(
            "application_dedup",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), index=True),
            sa.Column(
                "job_id",
                sa.String(64),
                sa.ForeignKey("jobs.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column("ats_provider", sa.String(50), nullable=True),
            sa.Column("application_url", sa.Text(), nullable=True),
            sa.Column(
                "applied_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint(
                "user_id", "job_id", name="uq_application_dedup_user_job"
            ),
        )

    # ------------------------------------------------------------------
    # A4 - Dedup Feedback
    # ------------------------------------------------------------------
    if not _table_exists("dedup_feedback"):
        op.create_table(
            "dedup_feedback",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "job_a_id",
                sa.String(64),
                sa.ForeignKey("jobs.id"),
                nullable=False,
            ),
            sa.Column(
                "job_b_id",
                sa.String(64),
                sa.ForeignKey("jobs.id"),
                nullable=False,
            ),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("is_duplicate", sa.Boolean(), nullable=False),
            sa.Column("title_similarity", sa.Float(), nullable=True),
            sa.Column("company_ratio", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "idx_dedup_feedback_pair", "dedup_feedback", ["job_a_id", "job_b_id"]
        )
        op.create_index("idx_dedup_feedback_user", "dedup_feedback", ["user_id"])

    # ------------------------------------------------------------------
    # F5 - Email Logs
    # ------------------------------------------------------------------
    if not _table_exists("email_logs"):
        op.create_table(
            "email_logs",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), index=True),
            sa.Column("sender", sa.String(500), nullable=False),
            sa.Column("subject", sa.String(1000), nullable=False),
            sa.Column("parsed_action", sa.String(30), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column(
                "matched_application_id",
                sa.Uuid(),
                sa.ForeignKey("applications.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("company_extracted", sa.String(300), nullable=True),
            sa.Column("job_title_extracted", sa.String(500), nullable=True),
            sa.Column("raw_body_hash", sa.String(64), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column(
                "processed_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )

    # ------------------------------------------------------------------
    # F3 - Networking
    # ------------------------------------------------------------------
    if not _table_exists("contacts"):
        op.create_table(
            "contacts",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), index=True),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("company", sa.String(300), nullable=True),
            sa.Column("role", sa.String(300), nullable=True),
            sa.Column("relationship_strength", sa.Integer(), default=3),
            sa.Column("linkedin_url", sa.Text(), nullable=True),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("last_contacted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists("referral_requests"):
        op.create_table(
            "referral_requests",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), index=True),
            sa.Column(
                "contact_id",
                sa.Uuid(),
                sa.ForeignKey("contacts.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column(
                "job_id",
                sa.String(64),
                sa.ForeignKey("jobs.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column("status", sa.String(30), default="draft"),
            sa.Column("message_template", sa.Text(), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )

    # ------------------------------------------------------------------
    # D3 - ML Model Artifacts
    # ------------------------------------------------------------------
    if not _table_exists("ml_model_artifacts"):
        op.create_table(
            "ml_model_artifacts",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("model_name", sa.String(100), nullable=False),
            sa.Column("model_version", sa.Integer(), default=1),
            sa.Column("model_bytes", sa.LargeBinary(), nullable=False),
            sa.Column("n_samples", sa.Integer(), default=0),
            sa.Column("cv_accuracy", sa.Float(), nullable=True),
            sa.Column("positive_rate", sa.Float(), nullable=True),
            sa.Column("feature_names", sa.String(1000), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_ml_model_artifacts_user_model",
            "ml_model_artifacts",
            ["user_id", "model_name"],
        )

    # ------------------------------------------------------------------
    # D2 - Outcome Tracking
    # ------------------------------------------------------------------
    if not _table_exists("application_outcomes"):
        op.create_table(
            "application_outcomes",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "application_id",
                sa.Uuid(),
                sa.ForeignKey("applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("stage_reached", sa.String(30), nullable=True),
            sa.Column("rejection_reason", sa.String(50), nullable=True),
            sa.Column("rejection_stage", sa.String(30), nullable=True),
            sa.Column("days_to_response", sa.Integer(), nullable=True),
            sa.Column("offer_amount", sa.Integer(), nullable=True),
            sa.Column("offer_equity", sa.String(200), nullable=True),
            sa.Column("offer_total_comp", sa.Integer(), nullable=True),
            sa.Column("negotiated_amount", sa.Integer(), nullable=True),
            sa.Column("final_decision", sa.String(30), nullable=True),
            sa.Column("was_ghosted", sa.Boolean(), default=False),
            sa.Column("referral_used", sa.Boolean(), default=False),
            sa.Column("cover_letter_used", sa.Boolean(), default=False),
            sa.Column("application_method", sa.String(20), nullable=True),
            sa.Column("feedback_notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_application_outcomes_user_id", "application_outcomes", ["user_id"]
        )
        op.create_index(
            "ix_application_outcomes_application_id",
            "application_outcomes",
            ["application_id"],
            unique=True,
        )

    if not _table_exists("company_insights"):
        op.create_table(
            "company_insights",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column(
                "company_name", sa.String(200), nullable=False, index=True
            ),
            sa.Column("total_applications", sa.Integer(), default=0),
            sa.Column("callback_count", sa.Integer(), default=0),
            sa.Column("avg_response_days", sa.Float(), nullable=True),
            sa.Column("ghosted_count", sa.Integer(), default=0),
            sa.Column("ghost_rate", sa.Float(), default=0.0),
            sa.Column("rejection_rate", sa.Float(), default=0.0),
            sa.Column("offer_rate", sa.Float(), default=0.0),
            sa.Column("offers_received", sa.Integer(), default=0),
            sa.Column("avg_offer_amount", sa.Float(), nullable=True),
            sa.Column("interview_difficulty", sa.Float(), nullable=True),
            sa.Column("culture_notes", sa.Text(), nullable=True),
            sa.Column("last_applied_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_company_insights_user_company",
            "company_insights",
            ["user_id", "company_name"],
            unique=True,
        )

    # ------------------------------------------------------------------
    # Fix users.created_at / updated_at timezone
    # ------------------------------------------------------------------
    op.alter_column(
        "users",
        "created_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "users",
        "updated_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "updated_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "users",
        "created_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
    )
    for table in [
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
    ]:
        op.drop_table(table)
