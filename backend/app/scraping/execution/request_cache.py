from __future__ import annotations

from collections.abc import Mapping


def build_conditional_headers(
    etag: str | None,
    last_modified: str | None,
) -> dict[str, str]:
    headers: dict[str, str] = {}
    if etag and etag.strip():
        headers["If-None-Match"] = etag.strip()
    if last_modified and last_modified.strip():
        headers["If-Modified-Since"] = last_modified.strip()
    return headers


def extract_response_cache_headers(
    headers: Mapping[str, str] | None,
) -> tuple[str | None, str | None]:
    if not headers:
        return None, None

    normalized = {key.lower(): value for key, value in headers.items()}
    etag = normalized.get("etag")
    last_modified = normalized.get("last-modified")
    return _clean_header_value(etag), _clean_header_value(last_modified)


def _clean_header_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
