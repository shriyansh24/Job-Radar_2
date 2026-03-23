from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.predictor import (
    FEATURE_NAMES,
    MIN_SAMPLES,
    MatchPredictor,
    ModelStatus,
    PredictionResult,
)
from app.auth.models import User
from app.jobs.models import Job
from app.pipeline.models import Application


def _make_job_id(title: str, company: str) -> str:
    raw = f"{title}|{company}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _create_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="fakehash",
        display_name="Test User",
    )
    db.add(user)
    await db.flush()
    return user


async def _create_job(
    db: AsyncSession,
    user: User,
    title: str = "Software Engineer",
    company: str = "TestCo",
    source: str = "test",
    remote_type: str | None = "remote",
    experience_level: str | None = "senior",
    skills: list[str] | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    posted_days_ago: int = 3,
) -> Job:
    job_id = _make_job_id(f"{title}-{uuid.uuid4().hex[:6]}", company)
    posted_at = datetime.now(timezone.utc) - timedelta(days=posted_days_ago)
    job = Job(
        id=job_id,
        user_id=user.id,
        source=source,
        title=title,
        company_name=company,
        remote_type=remote_type,
        experience_level=experience_level,
        skills_required=skills or ["python", "fastapi"],
        salary_min=salary_min,
        salary_max=salary_max,
        posted_at=posted_at,
        scraped_at=posted_at,
    )
    db.add(job)
    await db.flush()
    return job


async def _create_application(
    db: AsyncSession,
    user: User,
    job: Job,
    status: str = "applied",
    source: str | None = None,
) -> Application:
    app = Application(
        id=uuid.uuid4(),
        user_id=user.id,
        job_id=job.id,
        company_name=job.company_name,
        position_title=job.title,
        status=status,
        source=source,
    )
    db.add(app)
    await db.flush()
    return app


async def _seed_training_data(
    db: AsyncSession,
    user: User,
    n_samples: int = 60,
) -> None:
    """Create jobs + applications with varied labels from application status."""
    positive_statuses = ["screening", "interviewing", "offer", "accepted"]
    negative_statuses = ["applied", "rejected", "withdrawn"]
    sources = ["linkedin", "company_site", "indeed"]

    for i in range(n_samples):
        title = f"Engineer {i}" if i % 2 == 0 else f"Manager {i}"
        company = f"Company{i % 10}"
        remote = "remote" if i % 3 == 0 else "hybrid" if i % 3 == 1 else "onsite"
        level = "senior" if i % 4 == 0 else "mid" if i % 4 == 1 else "junior"
        source = sources[i % len(sources)]

        job = await _create_job(
            db,
            user,
            title=title,
            company=company,
            source=source,
            remote_type=remote,
            experience_level=level,
            skills=["python", "sql"] if i % 2 == 0 else ["java"],
            salary_min=80000 if i % 3 == 0 else None,
            salary_max=150000 if i % 3 == 0 else None,
            posted_days_ago=i % 30,
        )

        # Make roughly 40% positive outcomes
        if i % 5 < 2:
            status = positive_statuses[i % len(positive_statuses)]
        else:
            status = negative_statuses[i % len(negative_statuses)]

        await _create_application(
            db,
            user,
            job,
            status=status,
            source="referral" if i % 7 == 0 else "manual",
        )

    await db.commit()


# -- Tests --


@pytest.mark.asyncio
async def test_feature_vector_has_correct_length(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await _create_job(db_session, user)
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    features = await predictor._build_features(user.id, job)

    assert len(features) == len(FEATURE_NAMES)
    assert len(features) == 8
    # All features should be floats
    for f in features:
        assert isinstance(f, float)


@pytest.mark.asyncio
async def test_train_insufficient_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    # Create only 5 samples (below MIN_SAMPLES)
    for i in range(5):
        job = await _create_job(db_session, user, title=f"Job {i}")
        await _create_application(db_session, user, job, status="applied")
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    result = await predictor.train(user.id)

    assert result.status == "insufficient_data"
    assert result.n_samples == 5
    assert result.cv_accuracy is None


@pytest.mark.asyncio
async def test_train_and_predict_full_cycle(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=60)

    predictor = MatchPredictor(db_session)

    # Train
    train_result = await predictor.train(user.id)
    assert train_result.status == "trained"
    assert train_result.n_samples >= MIN_SAMPLES
    assert train_result.cv_accuracy is not None
    assert 0.0 <= train_result.cv_accuracy <= 1.0
    assert train_result.positive_rate is not None
    assert train_result.model_version == 1

    # Predict on a new job
    new_job = await _create_job(
        db_session,
        user,
        title="Engineer 999",
        company="NewCorp",
        remote_type="remote",
        experience_level="senior",
    )
    await db_session.commit()

    pred_result = await predictor.predict(user.id, new_job.id)
    assert pred_result is not None
    assert isinstance(pred_result, PredictionResult)
    assert 0.0 <= pred_result.probability <= 1.0
    assert pred_result.confidence in ("high", "medium", "low")
    assert len(pred_result.top_features) > 0
    assert len(pred_result.top_features) <= 5
    assert pred_result.model_version == 1


@pytest.mark.asyncio
async def test_predict_without_trained_model(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await _create_job(db_session, user)
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    result = await predictor.predict(user.id, job.id)

    assert result is None


@pytest.mark.asyncio
async def test_predict_nonexistent_job(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=30)

    predictor = MatchPredictor(db_session)
    await predictor.train(user.id)

    result = await predictor.predict(user.id, "nonexistent_job_id")
    assert result is None


@pytest.mark.asyncio
async def test_predict_scopes_job_lookup_by_user_id(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    other_user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=30)
    other_job = await _create_job(db_session, other_user, title="Other User Job")
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    await predictor.train(user.id)

    result = await predictor.predict(user.id, other_job.id)
    assert result is None


@pytest.mark.asyncio
async def test_train_handles_single_class_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    for i in range(MIN_SAMPLES):
        job = await _create_job(db_session, user, title=f"Single Class Job {i}")
        await _create_application(db_session, user, job, status="applied")
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    result = await predictor.train(user.id)

    assert result.status == "insufficient_class_diversity"
    assert result.n_samples == MIN_SAMPLES
    assert result.cv_accuracy is None
    assert result.model_version == 0

    status = await predictor.get_model_status(user.id)
    assert status.is_trained is False


@pytest.mark.asyncio
async def test_train_handles_insufficient_minority_samples(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    for i in range(MIN_SAMPLES):
        job = await _create_job(db_session, user, title=f"Imbalanced Job {i}")
        status = "screening" if i == 0 else "applied"
        await _create_application(db_session, user, job, status=status)
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    result = await predictor.train(user.id)

    assert result.status == "insufficient_minority_samples"
    assert result.n_samples == MIN_SAMPLES
    assert result.cv_accuracy is None
    assert result.model_version == 0


@pytest.mark.asyncio
async def test_train_offloads_sklearn_work_to_threads(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=30)

    predictor = MatchPredictor(db_session)

    async def fake_run_sync(func, *args, **kwargs):
        return func(*args, **kwargs)

    with patch(
        "app.analytics.predictor.to_thread.run_sync",
        side_effect=fake_run_sync,
    ) as mocked_run_sync:
        result = await predictor.train(user.id)

    assert result.status == "trained"
    assert mocked_run_sync.await_count == 2


@pytest.mark.asyncio
async def test_model_status_untrained(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await db_session.commit()

    predictor = MatchPredictor(db_session)
    status = await predictor.get_model_status(user.id)

    assert isinstance(status, ModelStatus)
    assert status.is_trained is False
    assert status.model_version == 0
    assert status.feature_names == list(FEATURE_NAMES)


@pytest.mark.asyncio
async def test_model_status_after_training(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=60)

    predictor = MatchPredictor(db_session)
    await predictor.train(user.id)

    status = await predictor.get_model_status(user.id)

    assert status.is_trained is True
    assert status.model_version == 1
    assert status.n_samples >= MIN_SAMPLES
    assert status.cv_accuracy is not None
    assert len(status.feature_names) == len(FEATURE_NAMES)


@pytest.mark.asyncio
async def test_retrain_increments_version(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=60)

    predictor = MatchPredictor(db_session)

    result1 = await predictor.train(user.id)
    assert result1.model_version == 1

    # Reset cached model so it retrains fresh
    predictor._model = None
    predictor._artifact = None

    result2 = await predictor.train(user.id)
    assert result2.model_version == 2


@pytest.mark.asyncio
async def test_feature_contributions_sorted_by_importance(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _seed_training_data(db_session, user, n_samples=60)

    predictor = MatchPredictor(db_session)
    await predictor.train(user.id)

    job = await _create_job(db_session, user, title="Engineer Special")
    await db_session.commit()

    pred = await predictor.predict(user.id, job.id)
    assert pred is not None

    contributions = pred.top_features
    # Verify sorted by absolute contribution descending
    for i in range(len(contributions) - 1):
        assert abs(contributions[i].contribution) >= abs(
            contributions[i + 1].contribution
        )


@pytest.mark.asyncio
async def test_title_similarity_with_matching_titles(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)

    # Create past applications with "Software Engineer" titles
    for i in range(3):
        job = await _create_job(
            db_session, user, title=f"Software Engineer {i}"
        )
        await _create_application(db_session, user, job)
    await db_session.commit()

    predictor = MatchPredictor(db_session)

    # Test with a similar title
    sim = await predictor._title_similarity(user.id, "Software Engineer")
    assert sim > 0.3  # should have reasonable similarity

    # Test with a completely different title
    sim_diff = await predictor._title_similarity(user.id, "Chef de Cuisine")
    assert sim_diff < sim  # should be less similar


@pytest.mark.asyncio
async def test_location_match_values(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    predictor = MatchPredictor(db_session)

    remote_job = await _create_job(db_session, user, remote_type="remote")
    assert predictor._compute_location_match(remote_job) == 1.0

    hybrid_job = await _create_job(db_session, user, remote_type="hybrid")
    assert predictor._compute_location_match(hybrid_job) == 0.7

    onsite_job = await _create_job(db_session, user, remote_type="onsite")
    assert predictor._compute_location_match(onsite_job) == 0.4

    none_job = await _create_job(db_session, user, remote_type=None)
    assert predictor._compute_location_match(none_job) == 0.5


@pytest.mark.asyncio
async def test_freshness_decreases_with_age(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    predictor = MatchPredictor(db_session)

    fresh_job = await _create_job(db_session, user, posted_days_ago=0)
    old_job = await _create_job(db_session, user, posted_days_ago=60)

    fresh_score = predictor._compute_freshness(fresh_job)
    old_score = predictor._compute_freshness(old_job)

    assert fresh_score > old_score
    assert fresh_score >= 0.8
    assert old_score <= 0.3
