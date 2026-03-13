"""Test 3-model council scoring with mocked LLM responses."""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.resume.council import (
    DimensionScore,
    CouncilScore,
    evaluate_resume_council,
    _parse_model_response,
    _aggregate_scores,
    SCORING_DIMENSIONS,
    COUNCIL_MODELS,
)


class TestDimensionScore:
    def test_create(self):
        ds = DimensionScore(grade="A", score=90, rationale="Strong match", gaps=[], suggestions=[])
        assert ds.grade == "A"
        assert ds.score == 90

    def test_score_bounds(self):
        ds = DimensionScore(grade="B", score=75, rationale="Good", gaps=["gap1"], suggestions=["s1"])
        assert 0 <= ds.score <= 100


class TestCouncilScore:
    def test_create(self):
        dim = DimensionScore(grade="B", score=80, rationale="Good", gaps=[], suggestions=[])
        cs = CouncilScore(
            skill_alignment=dim,
            experience_level=dim,
            impact_language=dim,
            ats_keyword_density=dim,
            structural_quality=dim,
            cultural_signals=dim,
            growth_trajectory=dim,
            overall_grade="B",
            overall_score=80,
            top_gaps=[],
            missing_keywords=[],
            strong_points=[],
            suggested_bullets=[],
            council_consensus=0.9,
        )
        assert cs.overall_grade == "B"
        assert cs.council_consensus == 0.9


class TestScoringDimensions:
    def test_has_seven_dimensions(self):
        assert len(SCORING_DIMENSIONS) == 7
        expected = {"skill_alignment", "experience_level", "impact_language",
                    "ats_keyword_density", "structural_quality", "cultural_signals",
                    "growth_trajectory"}
        assert set(SCORING_DIMENSIONS) == expected


class TestCouncilModels:
    def test_has_three_models(self):
        assert len(COUNCIL_MODELS) == 3


class TestParseModelResponse:
    def test_valid_json(self):
        response = json.dumps({
            "skill_alignment": {"grade": "A", "score": 90, "rationale": "Strong", "gaps": [], "suggestions": []},
            "experience_level": {"grade": "B", "score": 75, "rationale": "Good", "gaps": [], "suggestions": []},
            "impact_language": {"grade": "B", "score": 80, "rationale": "Clear", "gaps": [], "suggestions": []},
            "ats_keyword_density": {"grade": "A", "score": 85, "rationale": "Well optimized", "gaps": [], "suggestions": []},
            "structural_quality": {"grade": "B", "score": 78, "rationale": "Good structure", "gaps": [], "suggestions": []},
            "cultural_signals": {"grade": "C", "score": 60, "rationale": "Weak", "gaps": ["team fit"], "suggestions": ["add"]},
            "growth_trajectory": {"grade": "B", "score": 70, "rationale": "OK", "gaps": [], "suggestions": []},
            "overall_grade": "B",
            "overall_score": 77,
            "top_gaps": ["gap1"],
            "missing_keywords": ["k1"],
            "strong_points": ["s1"],
            "suggested_bullets": ["b1"],
        })
        result = _parse_model_response(response)
        assert isinstance(result, dict)
        assert "skill_alignment" in result
        assert result["overall_score"] == 77

    def test_invalid_json_returns_none(self):
        result = _parse_model_response("not json at all")
        assert result is None

    def test_missing_fields_returns_partial(self):
        response = json.dumps({"skill_alignment": {"grade": "A", "score": 90, "rationale": "OK", "gaps": [], "suggestions": []}})
        result = _parse_model_response(response)
        assert result is not None  # Partial is OK


class TestAggregateScores:
    def test_average_scores(self):
        dim1 = {"grade": "A", "score": 90, "rationale": "Strong", "gaps": [], "suggestions": []}
        dim2 = {"grade": "B", "score": 70, "rationale": "OK", "gaps": [], "suggestions": []}
        dim3 = {"grade": "A", "score": 80, "rationale": "Good", "gaps": [], "suggestions": []}

        responses = [
            {d: dim1 for d in SCORING_DIMENSIONS} | {"overall_grade": "A", "overall_score": 90, "top_gaps": [], "missing_keywords": [], "strong_points": ["s1"], "suggested_bullets": []},
            {d: dim2 for d in SCORING_DIMENSIONS} | {"overall_grade": "B", "overall_score": 70, "top_gaps": ["g1"], "missing_keywords": ["k1"], "strong_points": [], "suggested_bullets": []},
            {d: dim3 for d in SCORING_DIMENSIONS} | {"overall_grade": "A", "overall_score": 80, "top_gaps": [], "missing_keywords": [], "strong_points": ["s2"], "suggested_bullets": ["b1"]},
        ]
        result = _aggregate_scores(responses)
        assert isinstance(result, CouncilScore)
        assert result.overall_score == 80  # average of 90, 70, 80
        assert result.council_consensus > 0

    def test_single_response(self):
        dim = {"grade": "B", "score": 75, "rationale": "Good", "gaps": [], "suggestions": []}
        responses = [
            {d: dim for d in SCORING_DIMENSIONS} | {"overall_grade": "B", "overall_score": 75, "top_gaps": [], "missing_keywords": [], "strong_points": [], "suggested_bullets": []},
        ]
        result = _aggregate_scores(responses)
        assert result.overall_score == 75
        assert result.council_consensus == 1.0  # Perfect consensus with one model

    def test_empty_responses_raises(self):
        with pytest.raises(ValueError):
            _aggregate_scores([])


@pytest.mark.asyncio
class TestEvaluateResumeCouncil:
    async def test_with_mocked_responses(self):
        dim = {"grade": "B", "score": 80, "rationale": "Good", "gaps": [], "suggestions": []}
        model_response = json.dumps(
            {d: dim for d in SCORING_DIMENSIONS} |
            {"overall_grade": "B", "overall_score": 80, "top_gaps": [], "missing_keywords": [],
             "strong_points": ["s1"], "suggested_bullets": ["b1"]}
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = model_response

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.resume.council._get_openrouter_client", return_value=mock_client):
            result = await evaluate_resume_council(
                "John Doe, 5 years Python", "Looking for senior Python dev", "test-key"
            )
            assert isinstance(result, CouncilScore)
            assert result.overall_score == 80

    async def test_empty_inputs_raises(self):
        with pytest.raises(ValueError):
            await evaluate_resume_council("", "", "key")
