from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_COMPOSE = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
DEV_COMPOSE = (REPO_ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
WORKER_ROLES = ("scraping", "analysis", "ops")


def _service_block(content: str, service_name: str) -> str:
    marker = f"  {service_name}:\n"
    start = content.index(marker) + len(marker)
    match = re.search(r"\n  [A-Za-z0-9_-]+:\n", content[start:])
    if match is None:
        return content[start:]
    return content[start : start + match.start()]


def test_base_compose_defines_queue_worker_services() -> None:
    for role in WORKER_ROLES:
        service_name = f"worker-{role}"
        body = _service_block(BASE_COMPOSE, service_name)

        assert f'command: ["python", "-m", "app.runtime.arq_worker", "{role}"]' in body
        assert f"JR_WORKER_ROLE: {role}" in body
        assert f"JR_WORKER_READY_MARKER: /tmp/jobradar-worker-{role}.ready" in body
        assert "migrate:" in body
        assert "service_completed_successfully" in body
        assert "postgres:" in body
        assert "service_healthy" in body
        assert "redis:" in body
        assert f'test: ["CMD-SHELL", "test -f /tmp/jobradar-worker-{role}.ready"]' in body
        assert "restart: unless-stopped" in body


def test_dev_overlay_defines_bind_mounted_queue_worker_services() -> None:
    for role in WORKER_ROLES:
        service_name = f"worker-{role}"
        body = _service_block(DEV_COMPOSE, service_name)

        assert "context: ./backend" in body
        assert "dockerfile: Dockerfile" in body
        assert "- ./backend:/app" in body
        assert f'command: ["python", "-m", "app.runtime.arq_worker", "{role}"]' in body
        assert 'JR_DEBUG: "true"' in body
        assert 'JR_TRUSTED_HOSTS: \'["localhost","127.0.0.1","backend","test"]\'' in body
        assert f"JR_WORKER_ROLE: {role}" in body
        assert f"JR_WORKER_READY_MARKER: /tmp/jobradar-worker-{role}.ready" in body
