from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.auto_apply.models import AutoApplyRule
    from app.jobs.models import Job


class RuleEngine:
    """Match jobs against auto-apply rules."""

    def match_jobs(
        self, jobs: list[Job], rules: list[AutoApplyRule]
    ) -> list[tuple[Job, AutoApplyRule]]:
        """Return jobs matched to their best rule (first match wins, highest priority)."""
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        matches: list[tuple[Job, AutoApplyRule]] = []
        for job in jobs:
            for rule in sorted_rules:
                if self._matches_rule(job, rule):
                    matches.append((job, rule))
                    break
        return matches

    def _matches_rule(self, job: Job, rule: AutoApplyRule) -> bool:
        """Check if a job matches a rule's criteria."""
        # Min match score
        if rule.min_match_score and (job.match_score or 0) < float(rule.min_match_score):
            return False

        # Required keywords (any must be in title or description)
        if rule.required_keywords:
            text = f"{job.title} {job.description_clean or ''}".lower()
            if not any(kw.lower() in text for kw in rule.required_keywords):
                return False

        # Excluded keywords
        if rule.excluded_keywords:
            text = f"{job.title} {job.description_clean or ''}".lower()
            if any(kw.lower() in text for kw in rule.excluded_keywords):
                return False

        # Required companies
        if rule.required_companies:
            if not any(
                c.lower() in (job.company_name or "").lower() for c in rule.required_companies
            ):
                return False

        # Excluded companies
        if rule.excluded_companies:
            if any(c.lower() in (job.company_name or "").lower() for c in rule.excluded_companies):
                return False

        # Experience levels
        if rule.experience_levels and job.experience_level:
            if job.experience_level not in rule.experience_levels:
                return False

        # Remote types
        if rule.remote_types and job.remote_type:
            if job.remote_type not in rule.remote_types:
                return False

        return True
