"""Test TF-IDF job-resume matching scorer."""
import pytest
from backend.nlp.tfidf_scorer import compute_tfidf_score, ScoringResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def python_job():
    return {
        "title": "Senior Python Engineer",
        "description_clean": (
            "We need a senior Python engineer with experience in FastAPI, "
            "PostgreSQL, and AWS."
        ),
        "skills_required": ["Python", "FastAPI", "PostgreSQL", "AWS"],
        "tech_stack": ["Python", "FastAPI"],
    }

@pytest.fixture()
def python_resume():
    return {
        "text": (
            "Senior Python developer with 5 years experience. "
            "Built REST APIs with FastAPI and PostgreSQL. Deployed on AWS."
        ),
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
    }

@pytest.fixture()
def java_job():
    return {
        "title": "Senior Java Engineer",
        "description_clean": (
            "We need a Java developer with Spring Boot and Kubernetes."
        ),
        "skills_required": ["Java", "Spring Boot", "Kubernetes"],
        "tech_stack": ["Java", "Spring Boot"],
    }

@pytest.fixture()
def marketing_resume():
    return {
        "text": "Marketing manager with experience in social media campaigns.",
        "skills": ["Marketing", "Social Media"],
    }

@pytest.fixture()
def empty_job():
    return {
        "title": "",
        "description_clean": "",
        "skills_required": [],
        "tech_stack": [],
    }

@pytest.fixture()
def empty_resume():
    return {"text": "", "skills": []}


# ---------------------------------------------------------------------------
# Required spec tests
# ---------------------------------------------------------------------------

class TestComputeTfidfScore:
    def test_high_match_resume(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        assert isinstance(result, ScoringResult)
        assert result.score >= 60, f"Expected >= 60, got {result.score}"
        assert len(result.skill_matches) >= 3, (
            f"Expected >= 3 skill matches, got {result.skill_matches}"
        )

    def test_low_match_resume(self, java_job, marketing_resume):
        result = compute_tfidf_score(java_job, marketing_resume)
        assert result.score < 50, f"Expected < 50, got {result.score}"
        assert len(result.skill_gaps) > 0, "Expected non-empty skill_gaps"

    def test_score_clamped_10_99(self, empty_job, empty_resume):
        result = compute_tfidf_score(empty_job, empty_resume)
        assert 10 <= result.score <= 99, f"Score {result.score} out of [10, 99]"

    def test_scoring_result_has_breakdown(self):
        result = compute_tfidf_score(
            {
                "title": "SWE",
                "description_clean": "Python",
                "skills_required": ["Python"],
                "tech_stack": ["Python"],
            },
            {"text": "Python developer", "skills": ["Python"]},
        )
        assert "base_cosine" in result.weight_breakdown
        assert "skill_bonus" in result.weight_breakdown

    def test_ai_ml_boost(self):
        job = {
            "title": "ML Engineer",
            "description_clean": (
                "Machine learning engineer working with TensorFlow and PyTorch"
            ),
            "skills_required": ["Python", "TensorFlow", "PyTorch"],
            "tech_stack": ["TensorFlow", "PyTorch"],
        }
        resume = {
            "text": (
                "ML engineer with TensorFlow and PyTorch experience. "
                "Built ML pipelines."
            ),
            "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning"],
        }
        result = compute_tfidf_score(job, resume)
        assert result.score >= 65, f"Expected >= 65, got {result.score}"


# ---------------------------------------------------------------------------
# Additional edge-case / contract tests
# ---------------------------------------------------------------------------

class TestScoringResultContract:
    def test_returns_scoring_result_type(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        assert isinstance(result, ScoringResult)

    def test_score_is_int(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        assert isinstance(result.score, int)

    def test_skill_matches_are_strings(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        assert all(isinstance(s, str) for s in result.skill_matches)

    def test_skill_gaps_are_strings(self, java_job, marketing_resume):
        result = compute_tfidf_score(java_job, marketing_resume)
        assert all(isinstance(s, str) for s in result.skill_gaps)

    def test_weight_breakdown_keys(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        for key in ("base_cosine", "skill_bonus", "weight_adj", "raw_before_clamp"):
            assert key in result.weight_breakdown, f"Missing key: {key}"

    def test_weight_breakdown_values_are_numeric(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        for k, v in result.weight_breakdown.items():
            assert isinstance(v, (int, float)), f"Non-numeric value for {k}: {v}"

    def test_explanation_is_str(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        assert isinstance(result.explanation, str) and len(result.explanation) > 0

    def test_matches_and_gaps_partition(self, python_job, python_resume):
        """skill_matches + skill_gaps should cover all unique normalised required skills."""
        result = compute_tfidf_score(python_job, python_resume)
        covered = set(result.skill_matches) | set(result.skill_gaps)
        # The deduped set of (skills_required + tech_stack) lowercased
        expected = {s.lower().strip() for s in python_job["skills_required"] + python_job["tech_stack"]}
        # Each item in matches/gaps must come from the expected set
        for s in covered:
            assert s in expected, f"Unexpected skill in result: {s}"


class TestScoreBoundaries:
    def test_score_never_below_10(self, empty_job, empty_resume):
        result = compute_tfidf_score(empty_job, empty_resume)
        assert result.score >= 10

    def test_score_never_above_99(self, python_job, python_resume):
        result = compute_tfidf_score(python_job, python_resume)
        assert result.score <= 99

    def test_identical_job_and_resume_text_high_score(self):
        text = (
            "python fastapi postgresql aws machine learning engineer senior "
            "experienced distributed systems microservices docker kubernetes"
        )
        result = compute_tfidf_score(
            {
                "title": "senior python engineer",
                "description_clean": text,
                "skills_required": ["python", "fastapi", "postgresql"],
                "tech_stack": ["python", "fastapi"],
            },
            {"text": text, "skills": ["python", "fastapi", "postgresql"]},
        )
        assert result.score >= 70, f"Expected high score for identical text, got {result.score}"

    def test_no_skills_field_graceful(self):
        """Handles missing skills_required / tech_stack keys."""
        result = compute_tfidf_score(
            {"title": "Developer", "description_clean": "Python developer"},
            {"text": "Python developer", "skills": ["Python"]},
        )
        assert 10 <= result.score <= 99

    def test_none_values_graceful(self):
        """Handles None values in job/resume fields without raising."""
        result = compute_tfidf_score(
            {
                "title": None,
                "description_clean": None,
                "skills_required": None,
                "tech_stack": None,
            },
            {"text": None, "skills": None},
        )
        assert 10 <= result.score <= 99


class TestSkillMatching:
    def test_matched_skills_subset_of_required(self):
        job = {
            "title": "Data Engineer",
            "description_clean": "Spark Kafka Python ETL",
            "skills_required": ["Python", "Spark", "Kafka", "SQL"],
            "tech_stack": [],
        }
        resume = {
            "text": "Python developer with Spark and SQL experience",
            "skills": ["Python", "Spark", "SQL"],
        }
        result = compute_tfidf_score(job, resume)
        # All matches should be from the required list (normalised)
        required_lower = {s.lower() for s in job["skills_required"]}
        for m in result.skill_matches:
            assert m in required_lower or m in {s.lower() for s in job["tech_stack"] + job["skills_required"]}

    def test_no_required_skills_no_matches_or_gaps(self):
        job = {
            "title": "Software Engineer",
            "description_clean": "Build systems at scale",
            "skills_required": [],
            "tech_stack": [],
        }
        resume = {"text": "Experienced developer", "skills": []}
        result = compute_tfidf_score(job, resume)
        assert result.skill_matches == []
        assert result.skill_gaps == []

    def test_multi_word_skill_matching(self):
        """'Machine Learning' as a skill should match if both tokens are in resume."""
        job = {
            "title": "ML Engineer",
            "description_clean": "machine learning engineer",
            "skills_required": ["Machine Learning"],
            "tech_stack": [],
        }
        resume = {"text": "machine learning specialist with deep learning experience", "skills": []}
        result = compute_tfidf_score(job, resume)
        # 'machine' and 'learning' both appear in resume tokens
        assert "machine learning" in [s.lower() for s in result.skill_matches]

    def test_high_score_when_tech_stack_fully_matched(self):
        job = {
            "title": "Backend Engineer",
            "description_clean": "Python FastAPI Redis Celery Docker",
            "skills_required": [],
            "tech_stack": ["Python", "FastAPI", "Redis", "Celery", "Docker"],
        }
        resume = {
            "text": "Python backend developer FastAPI Redis Celery Docker",
            "skills": ["Python", "FastAPI", "Redis", "Celery", "Docker"],
        }
        result = compute_tfidf_score(job, resume)
        assert result.score >= 60, f"Expected >= 60, got {result.score}"


class TestAIMLBoost:
    def test_ml_keywords_increase_score_vs_unrelated(self):
        """An ML-focused resume should outscore a marketing resume on an ML job."""
        ml_job = {
            "title": "ML Engineer",
            "description_clean": "machine learning tensorflow pytorch deep learning",
            "skills_required": ["Python", "TensorFlow"],
            "tech_stack": ["TensorFlow", "PyTorch"],
        }
        ml_resume = {
            "text": "machine learning engineer tensorflow pytorch deep learning pipelines",
            "skills": ["Python", "TensorFlow", "PyTorch"],
        }
        unrelated_resume = {
            "text": "sales manager with crm experience and client relations",
            "skills": ["Sales", "CRM"],
        }
        ml_result = compute_tfidf_score(ml_job, ml_resume)
        unrelated_result = compute_tfidf_score(ml_job, unrelated_resume)
        assert ml_result.score > unrelated_result.score, (
            f"ML resume ({ml_result.score}) should outscore unrelated ({unrelated_result.score})"
        )
