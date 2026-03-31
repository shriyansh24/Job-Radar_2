from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import asyncpg
import redis

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
BACKEND_ENV_FILE = BACKEND_ROOT / ".env"


def _normalize_scheme(url: str) -> str:
    if "://" not in url:
        return url
    scheme, remainder = url.split("://", 1)
    return f"{scheme.split('+', 1)[0]}://{remainder}"


def _load_backend_env_defaults() -> dict[str, str]:
    if not BACKEND_ENV_FILE.exists():
        return {}

    defaults: dict[str, str] = {}
    for raw_line in BACKEND_ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        defaults[key.strip()] = value.strip().strip("\"'")
    return defaults


async def _check_postgres(database_url: str) -> None:
    parsed = urlparse(_normalize_scheme(database_url))
    host = parsed.hostname
    port = parsed.port or 5432
    if not host:
        raise RuntimeError(f"Postgres URL does not include a host: {database_url!r}")

    try:
        connection = await asyncpg.connect(database_url.replace("+asyncpg", ""), timeout=3)
    except Exception as exc:
        raise RuntimeError(
            f"Postgres is not usable at {host}:{port}. "
            f"Check JR_DATABASE_URL or start the repo dependencies, for example "
            f"'docker compose up -d postgres redis'."
        ) from exc
    else:
        await connection.close()


def _check_redis(redis_url: str) -> None:
    parsed = urlparse(_normalize_scheme(redis_url))
    host = parsed.hostname
    port = parsed.port or 6379
    if not host:
        raise RuntimeError(f"Redis URL does not include a host: {redis_url!r}")

    client: redis.Redis | None = None
    try:
        client = redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3)
        client.ping()
    except Exception as exc:
        raise RuntimeError(
            f"Redis is not usable at {host}:{port}. "
            f"Check JR_REDIS_URL or start the repo dependencies, for example "
            f"'docker compose up -d postgres redis'."
        ) from exc
    finally:
        try:
            if client is not None:
                client.close()
        except Exception as exc:
            print(
                f"warning: failed to close Redis client cleanly during Playwright bootstrap: {exc}",
                file=sys.stderr,
            )


def main() -> int:
    backend_env_defaults = _load_backend_env_defaults()
    database_url = os.environ.get(
        "JR_DATABASE_URL",
        backend_env_defaults.get("JR_DATABASE_URL", ""),
    )
    redis_url = os.environ.get(
        "JR_REDIS_URL",
        backend_env_defaults.get("JR_REDIS_URL", ""),
    )

    if not database_url:
        raise RuntimeError("JR_DATABASE_URL must be set before starting the Playwright backend.")
    if not redis_url:
        raise RuntimeError("JR_REDIS_URL must be set before starting the Playwright backend.")

    asyncio.run(_check_postgres(database_url))
    _check_redis(redis_url)

    env = {**backend_env_defaults, **os.environ}

    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        check=True,
    )

    return subprocess.call(
        ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_ROOT,
        env=env,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
