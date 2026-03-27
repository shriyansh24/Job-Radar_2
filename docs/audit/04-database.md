# Database Audit - JobRadar V2

## DB-01 - HIGH: DateTime Columns Missing Timezone
- **Files:** Multiple models
- **Detail:** Fixed. The remaining audited runtime model columns are timezone-aware, and the migration pass normalizes the previously naive `users.*` and `jobs.expires_at` columns.
- **Evidence:** `backend/tests/contracts/models/test_sqlalchemy_model_contracts.py`, `backend/app/migrations/versions/20260321_db_audit_fixes.py`
- **Status:** FIXED

## DB-02 - HIGH: Nullable FKs Without Cascade
- **Files:** `backend/app/auto_apply/models.py`, `backend/app/copilot/models.py`, `backend/app/interview/models.py`, `backend/app/pipeline/models.py`
- **Detail:** Fixed. Nullable job foreign keys now specify `ondelete="SET NULL"` and the migration replaces the existing constraints accordingly.
- **Evidence:** `backend/tests/contracts/models/test_sqlalchemy_model_contracts.py`, `backend/app/migrations/versions/20260321_db_audit_fixes.py`
- **Status:** FIXED

## DB-03 - HIGH: No Connection Pool Configuration
- **File:** `backend/app/database.py`
- **Detail:** Fixed. Non-SQLite engines now use explicit pool sizing, overflow, pre-ping, and recycle settings.
- **Evidence:** `backend/tests/infra/test_database.py`
- **Status:** FIXED

## DB-04 - MEDIUM: Embedding Batch Partial Failures
- **File:** `backend/app/enrichment/embedding.py`
- **Detail:** Fixed. Embedding writes are now all-or-nothing per batch, with rollback on any failed row update.
- **Evidence:** `backend/tests/unit/intelligence/test_embedding_service.py`
- **Status:** FIXED

## DB-05 - MEDIUM: Migration Downgrade Pgvector Gap
- **File:** `backend/app/migrations/versions/002_create_all_tables.py`
- **Detail:** Fixed. The base schema downgrade now explicitly drops the `vector` extension after removing the tables and indexes that depend on it.
- **Evidence:** `backend/tests/migrations/test_alembic_revisions.py`
- **Status:** FIXED

## DB-06 - LOW: N+1 Query Patterns
- **File:** `backend/app/jobs/models.py`
- **Detail:** Fixed. `Job.applications` now uses `lazy="selectin"` instead of the default lazy loading.
- **Evidence:** `backend/tests/unit/jobs/test_job_model.py`
- **Status:** FIXED

## Verified Fixes Since Initial Audit

## DB-F01 - FIXED: Notification Timestamp ORM Type Did Not Match Schema
- **Files:** `backend/app/notifications/models.py`, `backend/tests/contracts/models/test_sqlalchemy_model_contracts.py`
- **Detail:** `Notification.created_at` is now explicitly `DateTime(timezone=True)` so the ORM contract matches the migration-defined database column.
- **Status:** FIXED
