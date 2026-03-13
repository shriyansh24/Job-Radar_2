"""Test skill gap analysis between resume and job description."""
import pytest
from backend.nlp.gap_analyzer import analyze_gaps, GapAnalysis


class TestGapAnalysis:
    @pytest.fixture
    def strong_resume(self):
        return {
            "text": "Senior Python developer with 5 years experience. Built REST APIs with FastAPI, PostgreSQL, and AWS. Led team of 5 engineers. Deployed ML models with TensorFlow.",
            "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "TensorFlow", "Docker", "Git"],
            "sections": {
                "experience": "Senior Engineer at Google. Built distributed systems. Led API redesign.",
                "skills": "Python, FastAPI, PostgreSQL, AWS, TensorFlow, Docker",
            },
        }

    @pytest.fixture
    def matching_job(self):
        return {
            "title": "Senior Python Engineer",
            "description_clean": "We need a senior Python engineer with experience in FastAPI, PostgreSQL, and AWS. Experience with ML frameworks is a plus.",
            "skills_required": ["Python", "FastAPI", "PostgreSQL", "AWS"],
            "skills_nice_to_have": ["TensorFlow", "Docker"],
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        }

    @pytest.fixture
    def mismatched_job(self):
        return {
            "title": "Senior Java Engineer",
            "description_clean": "We need a Java developer with Spring Boot, Kubernetes, and extensive microservices experience. Must have 7+ years Java.",
            "skills_required": ["Java", "Spring Boot", "Kubernetes", "Microservices"],
            "skills_nice_to_have": ["Kafka", "Terraform"],
            "tech_stack": ["Java", "Spring Boot", "Kubernetes"],
        }

    def test_high_match_has_many_matches(self, strong_resume, matching_job):
        result = analyze_gaps(strong_resume, matching_job)
        assert isinstance(result, GapAnalysis)
        assert len(result.matched_skills) >= 3
        assert len(result.missing_skills) == 0 or len(result.missing_skills) < len(result.matched_skills)

    def test_low_match_has_many_gaps(self, strong_resume, mismatched_job):
        result = analyze_gaps(strong_resume, mismatched_job)
        assert len(result.missing_skills) >= 2
        assert "Java" in result.missing_skills or "java" in [s.lower() for s in result.missing_skills]

    def test_transferable_skills_identified(self, strong_resume, mismatched_job):
        result = analyze_gaps(strong_resume, mismatched_job)
        # Python dev has transferable skills for Java role (e.g., general programming)
        assert isinstance(result.transferable_skills, list)

    def test_keyword_density_range(self, strong_resume, matching_job):
        result = analyze_gaps(strong_resume, matching_job)
        assert 0.0 <= result.keyword_density <= 1.0

    def test_experience_fit_range(self, strong_resume, matching_job):
        result = analyze_gaps(strong_resume, matching_job)
        assert 0.0 <= result.experience_fit <= 1.0

    def test_strongest_bullets(self, strong_resume, matching_job):
        result = analyze_gaps(strong_resume, matching_job)
        assert isinstance(result.strongest_bullets, list)

    def test_weakest_sections(self, strong_resume, mismatched_job):
        result = analyze_gaps(strong_resume, mismatched_job)
        assert isinstance(result.weakest_sections, list)

    def test_ats_suggestions(self, strong_resume, matching_job):
        result = analyze_gaps(strong_resume, matching_job)
        assert isinstance(result.ats_optimization_suggestions, list)

    def test_empty_resume(self):
        result = analyze_gaps({"text": "", "skills": [], "sections": {}}, {"title": "SWE", "description_clean": "Python dev", "skills_required": ["Python"], "skills_nice_to_have": [], "tech_stack": []})
        assert isinstance(result, GapAnalysis)
        assert len(result.missing_skills) > 0

    def test_empty_job(self):
        result = analyze_gaps({"text": "Python dev", "skills": ["Python"], "sections": {}}, {"title": "", "description_clean": "", "skills_required": [], "skills_nice_to_have": [], "tech_stack": []})
        assert isinstance(result, GapAnalysis)

    def test_matched_skills_have_confidence(self, strong_resume, matching_job):
        result = analyze_gaps(strong_resume, matching_job)
        if result.matched_skills:
            first = result.matched_skills[0]
            assert isinstance(first, dict)
            assert "skill" in first
            assert "confidence" in first
