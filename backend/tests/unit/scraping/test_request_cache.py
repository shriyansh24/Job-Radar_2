from __future__ import annotations

from app.scraping.execution.request_cache import (
    build_conditional_headers,
    extract_response_cache_headers,
)


def test_build_conditional_headers_omits_empty_values() -> None:
    assert build_conditional_headers(None, "   ") == {}


def test_build_conditional_headers_includes_etag_and_last_modified() -> None:
    headers = build_conditional_headers('"abc"', "Mon, 01 Jan 2026 00:00:00 GMT")
    assert headers == {
        "If-None-Match": '"abc"',
        "If-Modified-Since": "Mon, 01 Jan 2026 00:00:00 GMT",
    }


def test_extract_response_cache_headers_is_case_insensitive() -> None:
    etag, last_modified = extract_response_cache_headers(
        {"ETag": 'W/"123"', "Last-Modified": "Tue, 02 Jan 2026 00:00:00 GMT"}
    )
    assert etag == 'W/"123"'
    assert last_modified == "Tue, 02 Jan 2026 00:00:00 GMT"
