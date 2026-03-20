# tests/unit/scraping/test_constants.py
from app.scraping.constants import PRIORITY_INTERVALS, TIER_CONCURRENCY


def test_priority_intervals_complete():
    assert set(PRIORITY_INTERVALS.keys()) == {"watchlist", "hot", "warm", "cool"}
    assert PRIORITY_INTERVALS["watchlist"] == 120
    assert PRIORITY_INTERVALS["hot"] == 240
    assert PRIORITY_INTERVALS["warm"] == 360
    assert PRIORITY_INTERVALS["cool"] == 720


def test_tier_concurrency_defined():
    assert TIER_CONCURRENCY[0] == 50
    assert TIER_CONCURRENCY[1] == 30
    assert TIER_CONCURRENCY[2] == 8
    assert TIER_CONCURRENCY[3] == 3
