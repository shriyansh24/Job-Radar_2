"""PageCrawler — follows pagination across multi-page career listings.

Detects "Next" links via multiple strategies (rel="next", text content,
aria-label, URL patterns) and follows them up to configurable limits.
Designed to work with whatever fetcher tier successfully fetched page 1.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from urllib.parse import parse_qs, parse_qsl, urlencode, urljoin, urlparse, urlunparse

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class PaginationResult:
    """Aggregated output from a paginated crawl."""

    jobs: list[dict] = field(default_factory=list)
    pages_crawled: int = 0
    urls_visited: list[str] = field(default_factory=list)
    stopped_reason: str = "no_more_pages"  # no_more_pages | max_pages | max_jobs | error


# ---------------------------------------------------------------------------
# URL-pattern pagination helpers
# ---------------------------------------------------------------------------

_PATH_PAGE_RE = re.compile(r"/page/(\d+)(/|$)", re.IGNORECASE)


def _valid_href(href: str | None) -> bool:
    """Return True when href can be followed (not javascript:, mailto:, #)."""
    if not href or not href.strip():
        return False
    stripped = href.strip()
    return not stripped.startswith(("#", "javascript:", "mailto:"))


def _normalize_visit_url(url: str) -> str:
    """Normalize URLs so loop detection ignores fragments, slash noise, and param order."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
    return urlunparse(
        parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            path=path,
            query=query,
            fragment="",
        )
    )


# ---------------------------------------------------------------------------
# HTML-based next-URL detection (no third-party deps)
# ---------------------------------------------------------------------------

# Text-based patterns: exact text or text inside a link tag
# Matches: Next, Next Page, Next ›, »,  →, ›, >>
_NEXT_TEXT_PATTERNS = (
    "Next Page",
    "Next",
    "\u203a",  # ›
    "\u00bb",  # »
    "\u2192",  # →
    ">>",
)

# Regex to extract <a …> … </a> blocks efficiently
_ANCHOR_RE = re.compile(
    r"<a\b(?P<attrs>[^>]*)>(?P<text>[^<]*(?:<(?!/?a\b)[^<]*)*)</a>",
    re.IGNORECASE | re.DOTALL,
)
_HREF_ATTR_RE = re.compile(r'\bhref=["\']([^"\']+)["\']', re.IGNORECASE)
_ARIA_ATTR_RE = re.compile(r'\baria-label=["\']([^"\']+)["\']', re.IGNORECASE)


class PageCrawler:
    """Paginated crawler that follows "Next" links across career listing pages.

    Usage::

        crawler = PageCrawler(max_pages=5)
        result = await crawler.crawl(
            start_url="https://example.com/jobs",
            first_page_html=html,
            fetch_fn=my_fetcher,
            parse_fn=my_parser,
        )

    Args:
        max_pages: Hard upper limit on the number of pages to crawl
            (includes the first page already fetched).
        max_jobs: Stop following pages once this many jobs have been
            accumulated across all pages.
        delay: Seconds to wait between fetching subsequent pages.
            Helps respect the target site's rate limit.
    """

    def __init__(
        self,
        max_pages: int = 10,
        max_jobs: int = 500,
        delay: float = 1.5,
    ) -> None:
        self.max_pages = max_pages
        self.max_jobs = max_jobs
        self.delay = delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def crawl(
        self,
        start_url: str,
        first_page_html: str,
        fetch_fn: Callable[[str], Awaitable[str]],
        parse_fn: Callable[[str, str], list[dict]],
    ) -> PaginationResult:
        """Crawl a paginated career listing starting from an already-fetched page.

        Args:
            start_url: The URL of the first page (used as a base for
                resolving relative "Next" hrefs).
            first_page_html: HTML of the first page (already fetched by the
                caller; the crawler will NOT re-fetch it).
            fetch_fn: Async callable ``(url) -> html_str`` used to fetch all
                subsequent pages.  This should be the same fetcher that
                successfully fetched the first page.
            parse_fn: Callable ``(html, url) -> list[dict]`` that extracts
                job dicts from a page's HTML.

        Returns:
            A :class:`PaginationResult` with all jobs and crawl metadata.
        """
        result = PaginationResult()
        visited: set[str] = set()
        current_url = start_url
        current_visit_url = _normalize_visit_url(start_url)
        current_html = first_page_html
        result.stopped_reason = "no_more_pages"

        while True:
            # --- Guard against revisiting the same URL ---
            if current_visit_url in visited:
                logger.warning(
                    "page_crawler_loop_detected",
                    url=current_url,
                    pages_crawled=result.pages_crawled,
                )
                break

            visited.add(current_visit_url)
            result.urls_visited.append(current_visit_url)
            result.pages_crawled += 1

            # --- Extract jobs from current page ---
            try:
                page_jobs = parse_fn(current_html, current_url)
            except Exception as exc:
                logger.error(
                    "page_crawler_parse_error",
                    url=current_url,
                    error=str(exc),
                    page=result.pages_crawled,
                )
                result.stopped_reason = "error"
                page_jobs = []

            result.jobs.extend(page_jobs)
            logger.info(
                "page_crawler_page_done",
                url=current_url,
                page=result.pages_crawled,
                jobs_on_page=len(page_jobs),
                total_jobs=len(result.jobs),
            )

            # --- Check limits AFTER extracting jobs from current page ---
            if len(result.jobs) >= self.max_jobs:
                result.stopped_reason = "max_jobs"
                break

            if result.pages_crawled >= self.max_pages:
                result.stopped_reason = "max_pages"
                break

            # --- Detect next page URL ---
            next_url = self._detect_next_url(current_html, current_url)
            if not next_url:
                break
            next_visit_url = _normalize_visit_url(next_url)

            # --- Avoid refetching a URL we already have ---
            if next_visit_url in visited:
                break

            # --- Polite delay before fetching next page ---
            await asyncio.sleep(self.delay)

            # --- Fetch next page ---
            try:
                next_html = await fetch_fn(next_url)
            except Exception as exc:
                logger.error(
                    "page_crawler_fetch_error",
                    url=next_url,
                    error=str(exc),
                    page=result.pages_crawled + 1,
                )
                result.stopped_reason = "error"
                break

            current_url = next_url
            current_visit_url = next_visit_url
            current_html = next_html

        logger.info(
            "page_crawler_finished",
            start_url=start_url,
            pages_crawled=result.pages_crawled,
            total_jobs=len(result.jobs),
            stopped_reason=result.stopped_reason,
        )
        return result

    # ------------------------------------------------------------------
    # Next-URL detection
    # ------------------------------------------------------------------

    def _detect_next_url(self, html: str, current_url: str) -> str | None:
        """Detect the next-page URL from an HTML page.

        Strategies (in order of preference):
        1. ``<a rel="next" href="…">``
        2. Anchor text matching common "next" labels
        3. ``aria-label`` containing "next"
        4. URL pattern increment (``?page=N``, ``?offset=N``, ``/page/N``)

        Returns the absolute URL for the next page, or ``None`` if not found.
        """
        # Strategy 1 – rel="next"
        rel_next_url = self._strategy_rel_next(html, current_url)
        if rel_next_url:
            return rel_next_url

        # Parse anchors once and reuse for strategies 2 & 3
        anchors = _ANCHOR_RE.findall(html)  # list of (attrs_str, inner_text)

        # Strategy 2 – text-based next links
        text_next_url = self._strategy_text_based(anchors, current_url)
        if text_next_url:
            return text_next_url

        # Strategy 3 – aria-label
        aria_next_url = self._strategy_aria_label(anchors, current_url)
        if aria_next_url:
            return aria_next_url

        # Strategy 4 – URL-pattern increment (no anchor required)
        # Only applied when the current URL does NOT already carry a page
        # parameter.  If the URL already says ?page=3 and there is no HTML
        # "Next" link, that is a genuine end-of-pagination signal, not a
        # reason to blindly try ?page=4.
        return self._strategy_url_pattern(current_url)

    def _strategy_rel_next(self, html: str, current_url: str) -> str | None:
        """Strategy 1: <a rel="next" href="…"> or <link rel="next" …>."""
        # Also match <link rel="next"> (used by some paginated sites)
        link_re = re.compile(
            r'<(?:a|link)\b[^>]*\brel=["\']next["\'][^>]*>',
            re.IGNORECASE,
        )
        for tag_match in link_re.finditer(html):
            tag_str = tag_match.group(0)
            href_m = _HREF_ATTR_RE.search(tag_str)
            if href_m:
                href = href_m.group(1)
                if _valid_href(href):
                    return urljoin(current_url, href)
        return None

    def _strategy_text_based(
        self,
        anchors: list[tuple[str, str]],
        current_url: str,
    ) -> str | None:
        """Strategy 2: anchor inner text matches a known "next" label."""
        for attrs_str, inner_text in anchors:
            clean_text = re.sub(r"<[^>]+>", "", inner_text).strip()
            for pattern in _NEXT_TEXT_PATTERNS:
                if clean_text.lower() == pattern.lower():
                    href_m = _HREF_ATTR_RE.search(attrs_str)
                    if href_m:
                        href = href_m.group(1)
                        if _valid_href(href):
                            return urljoin(current_url, href)
        return None

    def _strategy_aria_label(
        self,
        anchors: list[tuple[str, str]],
        current_url: str,
    ) -> str | None:
        """Strategy 3: aria-label containing "next"."""
        for attrs_str, _inner_text in anchors:
            aria_m = _ARIA_ATTR_RE.search(attrs_str)
            if aria_m and "next" in aria_m.group(1).lower():
                href_m = _HREF_ATTR_RE.search(attrs_str)
                if href_m:
                    href = href_m.group(1)
                    if _valid_href(href):
                        return urljoin(current_url, href)
        return None

    def _strategy_url_pattern(self, current_url: str) -> str | None:
        """Strategy 4: increment page/offset parameter in the current URL.

        This is a last-resort heuristic applied **only** when the current URL
        does not already contain a page-number parameter.  If the URL already
        has ``?page=N`` and no HTML "Next" link was found, that is a genuine
        end-of-pagination signal — we must not blindly guess at page N+1.

        When the URL has no page param at all (e.g. ``/jobs``), we try adding
        ``?page=2`` to seed pagination for sites that omit the parameter on
        page 1.  For ``/page/N`` path segments we always increment since the
        path explicitly encodes the page number.
        """
        parsed = urlparse(current_url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        # ── Query-param page numbers ─────────────────────────────────────
        # Only fire when the param is already present at page=1 (first page
        # can legitimately say ?page=1) or entirely absent.
        for param in ("page", "p", "pg", "pagenum", "page_num"):
            if param in params:
                try:
                    current_page = int(params[param][0])
                except (ValueError, IndexError):
                    continue
                # If we're already past page 1, require an HTML signal instead
                # of blindly incrementing — otherwise we loop forever.
                if current_page > 1:
                    return None
                params[param] = [str(current_page + 1)]
                new_query = urlencode(
                    {k: v[0] if len(v) == 1 else v for k, v in params.items()},
                    doseq=True,
                )
                return urlunparse(parsed._replace(query=new_query))

        # ── Path-segment /page/N ─────────────────────────────────────────
        # Path-based pagination is safe to increment because the site has
        # explicitly structured its URLs this way.
        path_m = _PATH_PAGE_RE.search(parsed.path)
        if path_m:
            current_page = int(path_m.group(1))
            if current_page > 1:
                # Already past page 1; require an HTML "Next" signal.
                return None
            new_path = _PATH_PAGE_RE.sub(
                f"/page/{current_page + 1}\\2",
                parsed.path,
            )
            return urlunparse(parsed._replace(path=new_path))

        return None
