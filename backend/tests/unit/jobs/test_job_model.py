from __future__ import annotations

from app.jobs.models import Job


def test_job_applications_uses_selectin_loading():
    assert Job.applications.property.lazy == "selectin"
