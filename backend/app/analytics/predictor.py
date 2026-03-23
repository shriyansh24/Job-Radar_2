from __future__ import annotations

import pickle
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial

import numpy as np
import structlog
from anyio import to_thread
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_score
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.models import MLModelArtifact
from app.jobs.models import Job
from app.pipeline.models import Application

logger = structlog.get_logger()

MODEL_NAME = "match_predictor"
MIN_SAMPLES = 20
MIN_CLASS_SAMPLES = 2
POSITIVE_STATUSES = frozenset({"screening", "interviewing", "offer", "accepted"})
FEATURE_NAMES = [
    "title_similarity",
    "company_familiarity",
    "skill_overlap",
    "salary_match",
    "location_match",
    "experience_match",
    "job_freshness",
    "source_familiarity",
]


@dataclass
class FeatureContribution:
    feature: str
    value: float
    contribution: float


@dataclass
class PredictionResult:
    probability: float
    confidence: str
    top_features: list[FeatureContribution] = field(default_factory=list)
    model_version: int = 0
    n_training_samples: int = 0


@dataclass
class TrainResult:
    status: str
    n_samples: int = 0
    cv_accuracy: float | None = None
    positive_rate: float | None = None
    model_version: int = 0


@dataclass
class ModelStatus:
    is_trained: bool = False
    model_version: int = 0
    n_samples: int = 0
    cv_accuracy: float | None = None
    positive_rate: float | None = None
    trained_at: datetime | None = None
    feature_names: list[str] = field(default_factory=list)


class MatchPredictor:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._model: HistGradientBoostingClassifier | None = None
        self._artifact: MLModelArtifact | None = None

    async def _load_model(
        self, user_id: uuid.UUID
    ) -> HistGradientBoostingClassifier | None:
        if self._model is not None:
            return self._model

        result = await self.db.execute(
            select(MLModelArtifact)
            .where(
                MLModelArtifact.user_id == user_id,
                MLModelArtifact.model_name == MODEL_NAME,
            )
            .order_by(MLModelArtifact.model_version.desc())
            .limit(1)
        )
        artifact = result.scalar_one_or_none()
        if artifact is None:
            return None

        self._artifact = artifact
        # Model bytes are written by this application only (not user-supplied),
        # so pickle deserialization is safe here.
        self._model = pickle.loads(artifact.model_bytes)  # noqa: S301
        return self._model

    async def predict(
        self, user_id: uuid.UUID, job_id: str
    ) -> PredictionResult | None:
        model = await self._load_model(user_id)
        if model is None:
            return None

        result = await self.db.execute(
            select(Job).where(Job.id == job_id, Job.user_id == user_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None

        features = await self._build_features(user_id, job)
        feature_array = np.array([features])
        proba = float(model.predict_proba(feature_array)[0][1])

        # Determine confidence level
        if proba > 0.7 or proba < 0.3:
            confidence = "high"
        elif proba > 0.55 or proba < 0.45:
            confidence = "medium"
        else:
            confidence = "low"

        top_features = self._explain(model, features)

        return PredictionResult(
            probability=round(proba, 4),
            confidence=confidence,
            top_features=top_features,
            model_version=self._artifact.model_version if self._artifact else 0,
            n_training_samples=self._artifact.n_samples if self._artifact else 0,
        )

    async def train(self, user_id: uuid.UUID) -> TrainResult:
        rows = await self._get_training_data(user_id)
        if len(rows) < MIN_SAMPLES:
            return TrainResult(
                status="insufficient_data",
                n_samples=len(rows),
            )

        x_data = np.array([r["features"] for r in rows])
        y_data = np.array([r["label"] for r in rows])

        positive_rate = float(np.mean(y_data))
        label_counts = np.bincount(y_data.astype(int), minlength=2)
        present_classes = int(np.count_nonzero(label_counts))
        if present_classes < 2:
            return TrainResult(
                status="insufficient_class_diversity",
                n_samples=len(rows),
                positive_rate=positive_rate,
            )

        minority_samples = int(label_counts[label_counts > 0].min())
        if minority_samples < MIN_CLASS_SAMPLES:
            return TrainResult(
                status="insufficient_minority_samples",
                n_samples=len(rows),
                positive_rate=positive_rate,
            )

        model = HistGradientBoostingClassifier(
            max_iter=100,
            min_samples_leaf=max(5, len(rows) // 20),
            learning_rate=0.1,
            max_depth=4,
        )

        n_folds = min(5, max(2, len(rows) // 10), minority_samples)
        scores = await to_thread.run_sync(
            partial(
                cross_val_score,
                model,
                x_data,
                y_data,
                cv=n_folds,
                scoring="accuracy",
            )
        )
        cv_accuracy = float(np.mean(scores))

        await to_thread.run_sync(model.fit, x_data, y_data)

        # Determine version
        result = await self.db.execute(
            select(MLModelArtifact.model_version)
            .where(
                MLModelArtifact.user_id == user_id,
                MLModelArtifact.model_name == MODEL_NAME,
            )
            .order_by(MLModelArtifact.model_version.desc())
            .limit(1)
        )
        last_version = result.scalar_one_or_none() or 0
        new_version = last_version + 1

        # Pickle is used here to serialize the scikit-learn model object,
        # which cannot be represented in JSON. The bytes are stored in our
        # own database and only deserialized by this application.
        artifact = MLModelArtifact(
            user_id=user_id,
            model_name=MODEL_NAME,
            model_version=new_version,
            model_bytes=pickle.dumps(model),
            n_samples=len(rows),
            cv_accuracy=cv_accuracy,
            positive_rate=positive_rate,
            feature_names=",".join(FEATURE_NAMES),
        )
        self.db.add(artifact)
        await self.db.commit()

        self._model = model
        self._artifact = artifact

        logger.info(
            "model_trained",
            user_id=str(user_id),
            version=new_version,
            n_samples=len(rows),
            cv_accuracy=cv_accuracy,
        )

        return TrainResult(
            status="trained",
            n_samples=len(rows),
            cv_accuracy=cv_accuracy,
            positive_rate=positive_rate,
            model_version=new_version,
        )

    async def get_model_status(self, user_id: uuid.UUID) -> ModelStatus:
        result = await self.db.execute(
            select(MLModelArtifact)
            .where(
                MLModelArtifact.user_id == user_id,
                MLModelArtifact.model_name == MODEL_NAME,
            )
            .order_by(MLModelArtifact.model_version.desc())
            .limit(1)
        )
        artifact = result.scalar_one_or_none()
        if artifact is None:
            return ModelStatus(is_trained=False, feature_names=list(FEATURE_NAMES))

        return ModelStatus(
            is_trained=True,
            model_version=artifact.model_version,
            n_samples=artifact.n_samples,
            cv_accuracy=artifact.cv_accuracy,
            positive_rate=artifact.positive_rate,
            trained_at=artifact.created_at,
            feature_names=(
                artifact.feature_names.split(",") if artifact.feature_names else []
            ),
        )

    async def _get_training_data(
        self, user_id: uuid.UUID
    ) -> list[dict[str, object]]:
        result = await self.db.execute(
            select(Application, Job)
            .join(Job, Job.id == Application.job_id)
            .where(
                Application.user_id == user_id,
                Job.user_id == user_id,
            )
        )
        rows_raw = result.all()

        training_data: list[dict[str, object]] = []
        for application, job in rows_raw:
            label = 1 if self._is_positive_status(application.status) else 0
            features = await self._build_features(user_id, job, application)
            training_data.append({"features": features, "label": label})

        return training_data

    async def _build_features(
        self,
        user_id: uuid.UUID,
        job: Job,
        application: Application | None = None,
    ) -> list[float]:
        exclude_application_id = application.id if application is not None else None
        title_sim = await self._title_similarity(user_id, job.title or "")
        company_score = await self._company_familiarity(
            user_id,
            job.company_name or "",
            exclude_application_id=exclude_application_id,
        )
        skill_overlap = self._compute_skill_overlap(job)
        salary_match = self._compute_salary_match(job)
        location_match = self._compute_location_match(job)
        experience_match = self._compute_experience_match(job)
        freshness = self._compute_freshness(job)
        source_score = await self._source_familiarity(
            user_id,
            job.source or "",
            exclude_application_id=exclude_application_id,
        )

        return [
            title_sim,
            company_score,
            skill_overlap,
            salary_match,
            location_match,
            experience_match,
            freshness,
            source_score,
        ]

    async def _title_similarity(
        self, user_id: uuid.UUID, job_title: str
    ) -> float:
        result = await self.db.execute(
            select(Application.position_title)
            .where(
                Application.user_id == user_id,
                Application.position_title.isnot(None),
            )
            .limit(50)
        )
        past_titles = [r[0] for r in result.all() if r[0]]

        if not past_titles or not job_title:
            return 0.5

        job_words = set(job_title.lower().split())
        best_sim = 0.0
        for title in past_titles:
            title_words = set(title.lower().split())
            if not job_words or not title_words:
                continue
            overlap = len(job_words & title_words)
            union = len(job_words | title_words)
            sim = overlap / union if union > 0 else 0.0
            best_sim = max(best_sim, sim)

        return best_sim

    async def _company_familiarity(
        self,
        user_id: uuid.UUID,
        company_name: str,
        exclude_application_id: uuid.UUID | None = None,
    ) -> float:
        if not company_name:
            return 0.0

        query = select(Application.status).where(
            Application.user_id == user_id,
            Application.company_name == company_name,
        )
        if exclude_application_id is not None:
            query = query.where(Application.id != exclude_application_id)

        result = await self.db.execute(query)
        statuses = [row[0] for row in result.all() if row[0]]

        return self._historical_success_score(statuses)

    async def _source_familiarity(
        self,
        user_id: uuid.UUID,
        source_name: str,
        exclude_application_id: uuid.UUID | None = None,
    ) -> float:
        if not source_name:
            return 0.0

        query = (
            select(Application.status)
            .join(Job, Job.id == Application.job_id)
            .where(
                Application.user_id == user_id,
                Job.user_id == user_id,
                Job.source == source_name,
            )
        )
        if exclude_application_id is not None:
            query = query.where(Application.id != exclude_application_id)

        result = await self.db.execute(query)
        statuses = [row[0] for row in result.all() if row[0]]
        return self._historical_success_score(statuses)

    def _historical_success_score(self, statuses: list[str]) -> float:
        if not statuses:
            return 0.0

        positive_count = sum(1 for status in statuses if self._is_positive_status(status))
        return max(0.1, positive_count / len(statuses))

    def _is_positive_status(self, status: str | None) -> bool:
        return status in POSITIVE_STATUSES

    def _compute_skill_overlap(self, job: Job) -> float:
        skills = job.skills_required or []
        if not skills:
            return 0.5
        return min(1.0, len(skills) / 10.0)

    def _compute_salary_match(self, job: Job) -> float:
        if job.salary_min is not None and job.salary_max is not None:
            salary_range = float(job.salary_max) - float(job.salary_min)
            midpoint = (float(job.salary_min) + float(job.salary_max)) / 2
            if midpoint > 0:
                return min(1.0, 1.0 - (salary_range / midpoint / 2))
        if job.salary_max is not None:
            return 0.7
        return 0.5

    def _compute_location_match(self, job: Job) -> float:
        if job.remote_type == "remote":
            return 1.0
        if job.remote_type == "hybrid":
            return 0.7
        if job.remote_type in ("onsite", "on-site"):
            return 0.4
        return 0.5

    def _compute_experience_match(self, job: Job) -> float:
        if job.experience_level is None:
            return 0.5

        level_map = {
            "entry": 0.3,
            "junior": 0.4,
            "mid": 0.6,
            "senior": 0.8,
            "lead": 0.9,
            "principal": 0.95,
            "staff": 0.95,
            "director": 0.9,
            "vp": 0.85,
            "executive": 0.8,
        }
        return level_map.get(job.experience_level.lower(), 0.5)

    def _compute_freshness(self, job: Job) -> float:
        if job.posted_at is None:
            if job.scraped_at:
                posted = job.scraped_at
            else:
                return 0.5
        else:
            posted = job.posted_at

        now = datetime.now(timezone.utc)
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)

        days_old = (now - posted).total_seconds() / 86400
        if days_old <= 1:
            return 1.0
        if days_old <= 7:
            return 0.8
        if days_old <= 14:
            return 0.6
        if days_old <= 30:
            return 0.4
        return 0.2

    def _explain(
        self,
        model: HistGradientBoostingClassifier,
        features: list[float],
    ) -> list[FeatureContribution]:
        # Compute marginal contribution of each feature by zeroing it out
        # and measuring the change in predicted probability.
        base_proba = float(
            model.predict_proba(np.array([features]))[0][1]
        )
        contributions: list[FeatureContribution] = []

        for i, name in enumerate(FEATURE_NAMES):
            if i >= len(features):
                break
            perturbed = list(features)
            perturbed[i] = 0.0
            perturbed_proba = float(
                model.predict_proba(np.array([perturbed]))[0][1]
            )
            delta = base_proba - perturbed_proba
            contributions.append(
                FeatureContribution(
                    feature=name,
                    value=round(features[i], 4),
                    contribution=round(delta, 4),
                )
            )

        contributions.sort(key=lambda c: abs(c.contribution), reverse=True)
        return contributions[:5]
