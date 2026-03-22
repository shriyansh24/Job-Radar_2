"""Unit tests for the PageCrawler pagination module.

Tests cover all detection strategies and crawl-control limits.
"""
from __future__ import annotations

import pytest

from app.scraping.execution.page_crawler import PageCrawler, PaginationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_html_with_rel_next(href: str) -> str:
    return f'<html><body><a rel="next" href="{href}">Next</a></body></html>'


def _make_html_with_text_link(text: str, href: str) -> str:
    return f'<html><body><a href="{href}">{text}</a></body></html>'


def _make_html_with_aria(href: str) -> str:
    return f'<html><body><a href="{href}" aria-label="Next page">›</a></body></html>'


def _make_html_no_pagination() -> str:
    return '<html><body><p>No jobs here</p></body></html>'


def _noop_parse(html: str, url: str) -> list[dict]:
    """Parse function that always returns an empty list."""
    return []


def _one_job_parse(html: str, url: str) -> list[dict]:
    """Parse function that always returns one job per page."""
    return [{"title": "Engineer", "url": url}]


def _five_jobs_parse(html: str, url: str) -> list[dict]:
    """Parse function that returns 5 jobs per page."""
    return [{"title": f"Job {i}", "url": url} for i in range(5)]


# ---------------------------------------------------------------------------
# _detect_next_url  — unit-level strategy tests
# ---------------------------------------------------------------------------

class TestDetectNextUrl:
    def setup_method(self):
        self.crawler = PageCrawler()
        self.base = "https://example.com/jobs"

    def test_detect_next_url_rel_next(self):
        """Strategy 1: <a rel="next" href="/jobs?page=2"> is detected."""
        html = _make_html_with_rel_next("/jobs?page=2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_rel_next_absolute(self):
        """rel="next" with an absolute href is returned as-is."""
        html = _make_html_with_rel_next("https://other.com/jobs?page=2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://other.com/jobs?page=2"

    def test_detect_next_url_rel_next_link_tag(self):
        """<link rel="next"> (not just <a>) is also detected."""
        html = '<html><head><link rel="next" href="/jobs?page=2"/></head><body></body></html>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_rel_next_skips_hash(self):
        """A rel="next" href of '#' is not a valid next page."""
        html = '<a rel="next" href="#">Next</a>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result is None

    def test_detect_next_url_text_based_next(self):
        """Strategy 2: <a>Next</a> is detected."""
        html = _make_html_with_text_link("Next", "/jobs?page=2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_text_based_next_page(self):
        """Strategy 2: <a>Next Page</a> is detected."""
        html = _make_html_with_text_link("Next Page", "/jobs?page=2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_text_based_right_angle(self):
        """Strategy 2: <a>›</a> (U+203A) is detected."""
        html = _make_html_with_text_link("\u203a", "/page/2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/page/2"

    def test_detect_next_url_text_based_double_angle(self):
        """Strategy 2: <a>»</a> (U+00BB) is detected."""
        html = _make_html_with_text_link("\u00bb", "/page/2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/page/2"

    def test_detect_next_url_text_based_arrow(self):
        """Strategy 2: <a>→</a> (U+2192) is detected."""
        html = _make_html_with_text_link("\u2192", "/page/2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/page/2"

    def test_detect_next_url_text_based_gt_gt(self):
        """Strategy 2: <a>>></a> is detected."""
        html = _make_html_with_text_link(">>", "/page/2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/page/2"

    def test_detect_next_url_aria_label(self):
        """Strategy 3: <a aria-label="Next page"> is detected."""
        html = _make_html_with_aria("/jobs?page=2")
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_aria_label_case_insensitive(self):
        """Strategy 3: aria-label is matched case-insensitively."""
        html = '<a href="/jobs?page=2" aria-label="NEXT PAGE">›</a>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_aria_label_skips_prev(self):
        """Strategy 3: aria-label='Previous page' is NOT matched as next."""
        html = '<a href="/jobs?page=1" aria-label="Previous page">‹</a>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result is None

    def test_detect_next_url_none_found(self):
        """No pagination indicators returns None."""
        html = _make_html_no_pagination()
        result = self.crawler._detect_next_url(html, self.base)
        assert result is None

    def test_detect_next_url_none_when_only_prev(self):
        """Only a 'Previous' link present returns None."""
        html = '<a href="/jobs?page=1" aria-label="Previous page">Previous</a>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result is None

    def test_detect_next_url_url_pattern_page_param_page_one(self):
        """Strategy 4: ?page=1 in the URL is incremented when no HTML link found (page 1 only)."""
        url = "https://example.com/jobs?page=1"
        result = self.crawler._detect_next_url(_make_html_no_pagination(), url)
        assert result == "https://example.com/jobs?page=2"

    def test_detect_next_url_url_pattern_page_param_page_two_no_html(self):
        """Strategy 4: ?page=2 with no HTML link returns None (avoids blind looping)."""
        url = "https://example.com/jobs?page=2"
        result = self.crawler._detect_next_url(_make_html_no_pagination(), url)
        assert result is None

    def test_detect_next_url_url_pattern_path_segment_page_one(self):
        """Strategy 4: /page/1 path is incremented to /page/2 when on page 1."""
        url = "https://example.com/jobs/page/1"
        result = self.crawler._detect_next_url(_make_html_no_pagination(), url)
        assert result == "https://example.com/jobs/page/2"

    def test_detect_next_url_url_pattern_path_segment_page_two_no_html(self):
        """Strategy 4: /page/2 with no HTML link returns None (end of pagination)."""
        url = "https://example.com/jobs/page/2"
        result = self.crawler._detect_next_url(_make_html_no_pagination(), url)
        assert result is None

    def test_detect_next_url_prefers_html_over_url_pattern(self):
        """HTML rel=next takes priority over URL pattern increment."""
        html = '<a rel="next" href="/jobs?page=99">Next</a>'
        url = "https://example.com/jobs?page=2"
        result = self.crawler._detect_next_url(html, url)
        assert result == "https://example.com/jobs?page=99"

    def test_detect_next_url_javascript_href_skipped(self):
        """javascript: hrefs in rel=next are skipped."""
        html = '<a rel="next" href="javascript:void(0)">Next</a>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result is None

    def test_detect_next_url_mailto_href_skipped(self):
        """mailto: hrefs are skipped."""
        html = '<a href="mailto:jobs@example.com">Next</a>'
        result = self.crawler._detect_next_url(html, self.base)
        assert result is None


# ---------------------------------------------------------------------------
# crawl()  — integration-level tests using mocked fetch_fn / parse_fn
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_single_page_no_pagination():
    """A page with no next link results in a single-page crawl."""
    crawler = PageCrawler(delay=0)

    async def fetch(url: str) -> str:
        return _make_html_no_pagination()

    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html=_make_html_no_pagination(),
        fetch_fn=fetch,
        parse_fn=_one_job_parse,
    )

    assert result.pages_crawled == 1
    assert len(result.jobs) == 1
    assert result.stopped_reason == "no_more_pages"
    assert result.urls_visited == ["https://example.com/jobs"]


@pytest.mark.asyncio
async def test_crawl_follows_pages():
    """Crawler follows 3 pages and aggregates all jobs."""
    pages = {
        "https://example.com/jobs": (
            '<a rel="next" href="/jobs?page=2">Next</a>',
            [{"title": "Job A"}],
        ),
        "https://example.com/jobs?page=2": (
            '<a rel="next" href="/jobs?page=3">Next</a>',
            [{"title": "Job B"}, {"title": "Job C"}],
        ),
        "https://example.com/jobs?page=3": (
            _make_html_no_pagination(),
            [{"title": "Job D"}],
        ),
    }

    async def fetch(url: str) -> str:
        html, _ = pages[url]
        return html

    def parse(html: str, url: str) -> list[dict]:
        _, jobs = pages[url]
        return jobs

    crawler = PageCrawler(delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html=pages["https://example.com/jobs"][0],
        fetch_fn=fetch,
        parse_fn=parse,
    )

    assert result.pages_crawled == 3
    assert len(result.jobs) == 4
    assert {j["title"] for j in result.jobs} == {"Job A", "Job B", "Job C", "Job D"}
    assert result.stopped_reason == "no_more_pages"
    assert len(result.urls_visited) == 3


@pytest.mark.asyncio
async def test_crawl_respects_max_pages():
    """Crawler stops at max_pages even if more pages exist."""
    def _page_html(page: int) -> str:
        return f'<a rel="next" href="/jobs?page={page + 1}">Next</a>'

    async def fetch(url: str) -> str:
        # Extract page number and return next-link HTML
        from urllib.parse import urlparse, parse_qs
        params = parse_qs(urlparse(url).query)
        page = int(params.get("page", ["1"])[0])
        return _page_html(page)

    crawler = PageCrawler(max_pages=3, delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html=_page_html(1),
        fetch_fn=fetch,
        parse_fn=_one_job_parse,
    )

    assert result.pages_crawled == 3
    assert result.stopped_reason == "max_pages"


@pytest.mark.asyncio
async def test_crawl_respects_max_jobs():
    """Crawler stops when accumulated jobs reach max_jobs."""
    # 5 jobs per page, 20 pages of pagination
    def _page_html(page: int) -> str:
        return f'<a rel="next" href="/jobs?page={page + 1}">Next</a>'

    async def fetch(url: str) -> str:
        from urllib.parse import urlparse, parse_qs
        params = parse_qs(urlparse(url).query)
        page = int(params.get("page", ["1"])[0])
        return _page_html(page)

    crawler = PageCrawler(max_pages=20, max_jobs=12, delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html=_page_html(1),
        fetch_fn=fetch,
        parse_fn=_five_jobs_parse,
    )

    # 5 jobs per page → stops at page 3 (15 jobs >= 12), but max_jobs check
    # is performed AFTER extracting from a page, so we get exactly >= 12.
    assert len(result.jobs) >= 12
    assert result.stopped_reason == "max_jobs"
    # Should NOT have crawled all 20 pages
    assert result.pages_crawled < 20


@pytest.mark.asyncio
async def test_crawl_handles_fetch_error_gracefully():
    """If page 3 fetch fails, jobs from pages 1-2 are still returned."""
    calls: list[str] = []

    async def fetch(url: str) -> str:
        calls.append(url)
        if "page=3" in url:
            raise ConnectionError("Network error")
        # page=2 returns a link to page=3 so that the crawler tries to fetch it
        if "page=2" in url:
            return '<a rel="next" href="/jobs?page=3">Next</a>'
        return '<a rel="next" href="/jobs?page=2">Next</a>'

    def parse(html: str, url: str) -> list[dict]:
        return [{"title": "Job", "url": url}]

    crawler = PageCrawler(delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html='<a rel="next" href="/jobs?page=2">Next</a>',
        fetch_fn=fetch,
        parse_fn=parse,
    )

    assert result.pages_crawled == 2
    assert len(result.jobs) == 2
    assert result.stopped_reason == "error"


@pytest.mark.asyncio
async def test_crawl_does_not_revisit_urls():
    """Crawler stops if 'next' URL points back to the start (loop guard)."""
    call_count = 0

    async def fetch(url: str) -> str:
        nonlocal call_count
        call_count += 1
        # Always 'next' points to the same page → infinite loop trap
        return '<a rel="next" href="https://example.com/jobs">Next</a>'

    crawler = PageCrawler(max_pages=10, delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html='<a rel="next" href="https://example.com/jobs">Next</a>',
        fetch_fn=fetch,
        parse_fn=_one_job_parse,
    )

    # Should stop immediately on page 1 (next URL == start URL, already visited)
    assert result.pages_crawled == 1
    assert call_count == 0  # fetch_fn never called — the "next" was the start URL


@pytest.mark.asyncio
async def test_crawl_normalizes_urls_before_loop_detection():
    """Crawler should treat equivalent URLs as the same page."""
    fetch_calls: list[str] = []

    async def fetch(url: str) -> str:
        fetch_calls.append(url)
        return _make_html_no_pagination()

    crawler = PageCrawler(max_pages=10, delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs?page=1&sort=asc",
        first_page_html='<a rel="next" href="https://example.com/jobs/?sort=asc&page=1#fragment">Next</a>',
        fetch_fn=fetch,
        parse_fn=_one_job_parse,
    )

    assert result.pages_crawled == 1
    assert fetch_calls == []
    assert result.urls_visited == ["https://example.com/jobs?page=1&sort=asc"]


@pytest.mark.asyncio
async def test_crawl_parse_error_does_not_abort():
    """A parse exception on one page is caught; crawl continues."""
    pages = {
        "https://example.com/jobs": '<a rel="next" href="/jobs?page=2">Next</a>',
        "https://example.com/jobs?page=2": _make_html_no_pagination(),
    }
    parse_calls: list[str] = []

    async def fetch(url: str) -> str:
        return pages[url]

    def parse(html: str, url: str) -> list[dict]:
        parse_calls.append(url)
        if url == "https://example.com/jobs":
            raise RuntimeError("parse failed on page 1")
        return [{"title": "Job on page 2"}]

    crawler = PageCrawler(delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html=pages["https://example.com/jobs"],
        fetch_fn=fetch,
        parse_fn=parse,
    )

    assert result.pages_crawled == 2
    # Page 1 parse failed (0 jobs), page 2 returned 1 job
    assert len(result.jobs) == 1
    assert result.jobs[0]["title"] == "Job on page 2"


@pytest.mark.asyncio
async def test_crawl_result_is_pagination_result():
    """crawl() always returns a PaginationResult instance."""
    crawler = PageCrawler(delay=0)

    async def fetch(url: str) -> str:
        return _make_html_no_pagination()

    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html=_make_html_no_pagination(),
        fetch_fn=fetch,
        parse_fn=_noop_parse,
    )

    assert isinstance(result, PaginationResult)
    assert isinstance(result.jobs, list)
    assert isinstance(result.urls_visited, list)
    assert isinstance(result.pages_crawled, int)
    assert isinstance(result.stopped_reason, str)


@pytest.mark.asyncio
async def test_crawl_max_pages_one_only_first_page():
    """max_pages=1 means only the first (already-fetched) page is used."""
    fetch_calls: list[str] = []

    async def fetch(url: str) -> str:
        fetch_calls.append(url)
        return _make_html_no_pagination()

    crawler = PageCrawler(max_pages=1, delay=0)
    result = await crawler.crawl(
        start_url="https://example.com/jobs",
        first_page_html='<a rel="next" href="/jobs?page=2">Next</a>',
        fetch_fn=fetch,
        parse_fn=_one_job_parse,
    )

    assert result.pages_crawled == 1
    assert fetch_calls == []  # fetch_fn never called
    assert result.stopped_reason == "max_pages"
