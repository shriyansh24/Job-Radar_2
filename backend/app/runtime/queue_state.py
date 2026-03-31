from __future__ import annotations

import time
from dataclasses import dataclass

SCRAPING_QUEUE = "arq:queue:scraping"
ANALYSIS_QUEUE = "arq:queue:analysis"
OPS_QUEUE = "arq:queue:ops"

VALID_QUEUE_PRESSURES = frozenset({"nominal", "elevated", "saturated"})
VALID_QUEUE_ALERTS = frozenset({"clear", "watch", "backlog", "stalled"})

QUEUE_PRESSURE_THRESHOLDS: dict[str, tuple[int, int]] = {
    SCRAPING_QUEUE: (10, 25),
    ANALYSIS_QUEUE: (20, 50),
    OPS_QUEUE: (5, 15),
}

QUEUE_ALERT_AGE_THRESHOLDS_SECONDS: dict[str, tuple[int, int]] = {
    SCRAPING_QUEUE: (300, 1200),
    ANALYSIS_QUEUE: (180, 900),
    OPS_QUEUE: (120, 600),
}


@dataclass(frozen=True)
class QueueSnapshot:
    queue_name: str
    queue_depth: int
    queue_pressure: str
    oldest_job_age_seconds: int
    queue_alert: str


def classify_queue_pressure(queue_name: str, depth: int) -> str:
    elevated_threshold, saturated_threshold = QUEUE_PRESSURE_THRESHOLDS.get(queue_name, (10, 25))
    if depth >= saturated_threshold:
        return "saturated"
    if depth >= elevated_threshold:
        return "elevated"
    return "nominal"


def summarize_queue_pressures(queue_depths: dict[str, int]) -> dict[str, str]:
    return {
        queue_name: classify_queue_pressure(queue_name, depth)
        for queue_name, depth in queue_depths.items()
    }


def classify_queue_alert(queue_name: str, *, pressure: str, oldest_job_age_seconds: int) -> str:
    watch_age_seconds, stalled_age_seconds = QUEUE_ALERT_AGE_THRESHOLDS_SECONDS.get(
        queue_name, (180, 900)
    )
    if oldest_job_age_seconds >= stalled_age_seconds:
        return "stalled"
    if pressure == "saturated":
        return "backlog"
    if pressure == "elevated" or oldest_job_age_seconds >= watch_age_seconds:
        return "watch"
    return "clear"


def derive_overall_pressure(queue_pressures: dict[str, str]) -> str:
    if "saturated" in queue_pressures.values():
        return "saturated"
    if "elevated" in queue_pressures.values():
        return "elevated"
    return "nominal"


def derive_overall_alert(queue_alerts: dict[str, str]) -> str:
    if "stalled" in queue_alerts.values():
        return "stalled"
    if "backlog" in queue_alerts.values():
        return "backlog"
    if "watch" in queue_alerts.values():
        return "watch"
    return "clear"


def _current_unix_ms() -> int:
    return int(time.time() * 1000)


def _score_to_oldest_job_age_seconds(score: float | int | None) -> int:
    if score is None:
        return 0
    age_ms = max(_current_unix_ms() - int(score), 0)
    return age_ms // 1000
