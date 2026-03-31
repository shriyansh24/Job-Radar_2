"""Adaptive career page parser with fingerprint-based resilience.

Tries known CSS selectors for job listings, then falls back to heuristic
extraction. Designed to work with raw HTML strings (no Scrapling dependency).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import structlog
from bs4 import BeautifulSoup, Tag

logger = structlog.get_logger()
JsonObject = dict[str, Any]
JobListing = dict[str, str | None]

ANTI_BOT_MARKERS = (
    "checking your browser",
    "cloudflare",
    "cf-browser-verification",
    "ray id",
    "enable javascript and cookies",
    "just a moment",
)


@dataclass(frozen=True)
class ParserDiagnosis:
    """Explain which adaptive path matched a career page fixture."""

    strategy: str
    jobs_found: int
    signals: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

ADAPTIVE_SELECTORS = [
    ".job-listing",
    ".job-card",
    ".career-item",
    ".position-card",
    ".opening",
    "[data-job]",
    "[data-job-id]",
    ".jobs-list__item",
    ".job-post",
    "li.position",
    ".careers-list li",
    ".openings-list li",
    ".positions li",
    ".posting",
    ".job-board__item",
    ".careers-posting",
    "[data-posting-id]",
    ".lever-job",
    ".greenhouse-job",
]


class AdaptiveCareerParser:
    """Extract job listings from career page HTML using adaptive selectors."""

    def __init__(self, html: str, company_name: str = "", base_url: str = ""):
        self.html = html
        self.company_name = company_name
        self.base_url = base_url

    def extract(self) -> list[JobListing]:
        """Extract job listings from HTML and common embedded data sources."""
        soup = BeautifulSoup(self.html, "html.parser")

        results = self._extract_by_selectors(soup)
        if results:
            return self._dedupe(results)

        results = self._extract_json_ld(soup)
        if results:
            return self._dedupe(results)

        results = self._extract_embedded_jobs(soup)
        if results:
            return self._dedupe(results)

        return self._dedupe(self._extract_heuristic(soup))

    def diagnose(self) -> ParserDiagnosis:
        """Classify the page shape without changing extraction behavior.

        The diagnostics are used by fixture-based regression tests so we can
        tell the difference between a real parser miss, a JavaScript shell, and
        an anti-bot challenge page.
        """
        soup = BeautifulSoup(self.html, "html.parser")

        selector_hits = self._extract_by_selectors(soup)
        if selector_hits:
            return ParserDiagnosis(
                strategy="selector",
                jobs_found=len(selector_hits),
                signals=("selector_match",),
            )

        json_ld_hits = self._extract_json_ld(soup)
        if json_ld_hits:
            return ParserDiagnosis(
                strategy="json_ld",
                jobs_found=len(json_ld_hits),
                signals=("json_ld_match",),
            )

        embedded_hits = self._extract_embedded_jobs(soup)
        if embedded_hits:
            return ParserDiagnosis(
                strategy="embedded_state",
                jobs_found=len(embedded_hits),
                signals=("embedded_state_match",),
            )

        heuristic_hits = self._dedupe(self._extract_heuristic(soup))
        if heuristic_hits:
            return ParserDiagnosis(
                strategy="heuristic",
                jobs_found=len(heuristic_hits),
                signals=("heuristic_match",),
            )

        challenge_signals = self._anti_bot_signals(soup)
        if challenge_signals:
            return ParserDiagnosis(
                strategy="anti_bot_challenge",
                jobs_found=0,
                signals=challenge_signals,
            )

        if self._looks_like_js_shell(soup):
            return ParserDiagnosis(
                strategy="js_shell_blank",
                jobs_found=0,
                signals=("js_shell",),
                notes=("No structured job payloads or selectable job cards were found.",),
            )

        return ParserDiagnosis(
            strategy="no_job_signal",
            jobs_found=0,
            notes=(
                "No adaptive parser path matched and no obvious challenge markers were found.",
            ),
        )

    def _extract_by_selectors(self, soup: BeautifulSoup) -> list[JobListing]:
        listings: list[JobListing] = []

        for selector in ADAPTIVE_SELECTORS:
            elements = soup.select(selector)
            if not elements:
                continue

            for el in elements:
                listing = self._parse_element(el)
                if listing and listing.get("title"):
                    listings.append(listing)

            if listings:
                logger.debug(
                    "adaptive_parser.selector_match",
                    selector=selector,
                    count=len(listings),
                )
                break

        return listings

    def _extract_json_ld(self, soup: BeautifulSoup) -> list[JobListing]:
        listings: list[JobListing] = []

        for script in soup.find_all("script", type="application/ld+json"):
            raw_payload = script.string or script.get_text()
            if not raw_payload or not raw_payload.strip():
                continue

            try:
                payload: object = json.loads(raw_payload)
            except json.JSONDecodeError as exc:
                logger.debug("adaptive_parser.invalid_json_ld", error=str(exc))
                continue

            for candidate in self._iter_job_payloads(payload):
                listing = self._normalize_payload_job(candidate)
                if listing is not None:
                    listings.append(listing)

        if listings:
            logger.debug("adaptive_parser.json_ld_match", count=len(listings))
        return listings

    def _extract_embedded_jobs(self, soup: BeautifulSoup) -> list[JobListing]:
        listings: list[JobListing] = []

        for script in soup.find_all("script"):
            script_type = self._attribute_as_string(script.get("type"))
            if script.get("src") or script_type == "application/ld+json":
                continue

            raw_payload = script.string or script.get_text()
            if not raw_payload or "job" not in raw_payload.lower():
                continue

            for payload in self._parse_embedded_payloads(
                raw_payload,
                script_type=script_type,
            ):
                for candidate in self._iter_embedded_job_candidates(payload):
                    listing = self._normalize_payload_job(candidate)
                    if listing is not None:
                        listings.append(listing)

        if listings:
            logger.debug("adaptive_parser.embedded_state_match", count=len(listings))
        return listings

    def _parse_element(self, el: Tag) -> JobListing:
        link = el.select_one("a")
        heading = el.select_one("h1, h2, h3, h4, h5, h6")

        title = ""
        if heading:
            title = heading.get_text(strip=True)
        elif link:
            title = link.get_text(strip=True)

        url = ""
        if link:
            href = self._attribute_as_string(link.get("href"))
            if href:
                url = urljoin(self.base_url, href)

        location = ""
        for loc_cls in ("location", "place", "city", "loc"):
            loc_els = el.select(f"[class*='{loc_cls}']")
            if loc_els:
                location = loc_els[0].get_text(strip=True)
                break

        department = None
        for dept_cls in ("department", "team", "group", "dept"):
            dept_els = el.select(f"[class*='{dept_cls}']")
            if dept_els:
                department = dept_els[0].get_text(strip=True)
                break

        return {
            "title": title,
            "url": url,
            "company_name": self.company_name,
            "location": location,
            "department": department,
            "description_raw": "",
        }

    def _iter_job_payloads(self, payload: object) -> Iterator[JsonObject]:
        if isinstance(payload, list):
            for item in payload:
                yield from self._iter_job_payloads(item)
            return

        if not isinstance(payload, dict):
            return

        payload_type = str(payload.get("@type", "")).lower()
        if payload_type == "jobposting":
            yield payload
            return

        for value in payload.values():
            yield from self._iter_job_payloads(value)

    def _parse_embedded_payloads(
        self,
        raw_payload: str,
        *,
        script_type: str | None,
    ) -> list[object]:
        payloads: list[object] = []
        stripped = raw_payload.strip()

        if script_type == "application/json" or stripped.startswith(("{", "[")):
            parsed = self._try_load_json(stripped)
            if parsed is not None:
                payloads.append(parsed)

        for marker in (
            "window.__INITIAL_STATE__",
            "__INITIAL_STATE__",
            "window.__NEXT_DATA__",
            "__NEXT_DATA__",
            "window.__NUXT__",
            "__NUXT__",
        ):
            marker_index = raw_payload.find(marker)
            if marker_index == -1:
                continue
            extracted = self._extract_balanced_json(raw_payload, marker_index + len(marker))
            if extracted is None:
                continue
            parsed = self._try_load_json(extracted)
            if parsed is not None:
                payloads.append(parsed)

        return payloads

    def _iter_embedded_job_candidates(self, payload: object) -> Iterator[JsonObject]:
        if isinstance(payload, list):
            for item in payload:
                yield from self._iter_embedded_job_candidates(item)
            return

        if not isinstance(payload, dict):
            return

        if self._looks_like_embedded_job(payload):
            yield payload

        for value in payload.values():
            yield from self._iter_embedded_job_candidates(value)

    def _normalize_payload_job(self, payload: JsonObject) -> JobListing | None:
        title = self._first_string(payload, "title", "name", "jobTitle", "positionTitle")
        if not title:
            return None

        raw_url = self._first_string(payload, "url", "applyUrl", "jobUrl", "href", "path")
        url = urljoin(self.base_url, raw_url) if raw_url else ""
        company_name = (
            self._first_string(payload, "company_name", "companyName")
            or self.company_name
        )

        hiring_org = payload.get("hiringOrganization")
        if not company_name and isinstance(hiring_org, dict):
            company_name = self._first_string(hiring_org, "name") or self.company_name

        return {
            "title": title,
            "url": url,
            "company_name": company_name,
            "location": self._extract_location(payload),
            "department": self._first_string(payload, "department", "team", "group", "function"),
            "description_raw": self._first_string(payload, "description", "summary") or "",
        }

    def _extract_location(self, payload: JsonObject) -> str:
        direct_location = self._first_string(payload, "location", "jobLocationText")
        if direct_location:
            return direct_location

        if payload.get("jobLocationType") == "TELECOMMUTE" or payload.get("remote") is True:
            return "Remote"

        job_location = payload.get("jobLocation")
        if isinstance(job_location, list):
            for entry in job_location:
                if isinstance(entry, dict):
                    location = self._extract_location(entry)
                    if location:
                        return location
        if isinstance(job_location, dict):
            address = job_location.get("address")
            if isinstance(address, dict):
                locality = self._first_string(address, "addressLocality", "city")
                region = self._first_string(address, "addressRegion", "state")
                country = self._first_string(address, "addressCountry", "country")
                parts = [part for part in (locality, region, country) if part]
                if parts:
                    return ", ".join(parts)

        locality = self._first_string(payload, "city")
        region = self._first_string(payload, "state", "region")
        country = self._first_string(payload, "country")
        parts = [part for part in (locality, region, country) if part]
        return ", ".join(parts)

    def _looks_like_embedded_job(self, payload: JsonObject) -> bool:
        if str(payload.get("@type", "")).lower() == "jobposting":
            return True

        title = self._first_string(payload, "title", "name", "jobTitle", "positionTitle")
        if not title:
            return False

        job_shape_keys = {
            "url",
            "applyurl",
            "joburl",
            "href",
            "path",
            "location",
            "joblocation",
            "department",
            "employmenttype",
            "jobid",
            "job_id",
            "requisitionid",
            "requisition_id",
        }
        payload_keys = {str(key).lower() for key in payload}
        return bool(payload_keys & job_shape_keys)

    def _dedupe(self, listings: list[JobListing]) -> list[JobListing]:
        deduped: list[JobListing] = []
        seen_keys: set[tuple[str, str]] = set()

        for listing in listings:
            title = str(listing.get("title", "")).strip()
            url = str(listing.get("url", "")).strip()
            if not title:
                continue
            dedupe_key = (title.lower(), url.lower())
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            deduped.append(listing)

        return deduped

    @staticmethod
    def _first_string(payload: JsonObject, *keys: str) -> str | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    return stripped
        return None

    @staticmethod
    def _try_load_json(raw_payload: str) -> object | None:
        try:
            parsed: object = json.loads(raw_payload)
            return parsed
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _attribute_as_string(value: object) -> str | None:
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _extract_balanced_json(raw_payload: str, start_index: int) -> str | None:
        opening_index = -1
        opening_char = ""
        closing_char = ""

        for index in range(start_index, len(raw_payload)):
            char = raw_payload[index]
            if char == "{":
                opening_index = index
                opening_char = "{"
                closing_char = "}"
                break
            if char == "[":
                opening_index = index
                opening_char = "["
                closing_char = "]"
                break

        if opening_index == -1:
            return None

        depth = 0
        in_string = False
        escape = False

        for index in range(opening_index, len(raw_payload)):
            char = raw_payload[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char == opening_char:
                depth += 1
                continue

            if char == closing_char:
                depth -= 1
                if depth == 0:
                    return raw_payload[opening_index : index + 1]

        return None

    def _extract_heuristic(self, soup: BeautifulSoup) -> list[JobListing]:
        """Fallback: find all links that look like job postings."""
        listings: list[JobListing] = []
        job_keywords = ("job", "career", "position", "opening", "role", "apply")

        for link in soup.find_all("a", href=True):
            href = self._attribute_as_string(link.get("href"))
            if not href:
                continue
            text = link.get_text(strip=True)
            href_lower = href.lower()

            if any(kw in href_lower for kw in job_keywords) and len(text) > 5:
                listings.append(
                    {
                        "title": text,
                        "url": urljoin(self.base_url, href),
                        "company_name": self.company_name,
                        "location": "",
                        "description_raw": "",
                    }
                )

        return listings

    @staticmethod
    def _anti_bot_signals(soup: BeautifulSoup) -> tuple[str, ...]:
        text = soup.get_text(" ", strip=True).lower()
        signals = [marker for marker in ANTI_BOT_MARKERS if marker in text]

        for script in soup.find_all("script"):
            payload = (script.string or script.get_text() or "").lower()
            if "_cf_chl_opt" in payload and "cloudflare" not in signals:
                signals.append("cloudflare")
            if "turnstile" in payload and "cf-browser-verification" not in signals:
                signals.append("cf-browser-verification")

        return tuple(dict.fromkeys(signals))

    @staticmethod
    def _looks_like_js_shell(soup: BeautifulSoup) -> bool:
        if soup.find(id="__next") is not None:
            return True
        if soup.find(id="__nuxt") is not None:
            return True
        if soup.find(attrs={"data-reactroot": True}) is not None:
            return True

        script_text = " ".join(
            (script.string or script.get_text() or "") for script in soup.find_all("script")
        ).lower()
        js_shell_markers = (
            "__next_data__",
            "__nuxt__",
            "window.__initial_state__",
            "fetch('/api/",
            'fetch("/api/',
            "renderjobs",
        )
        return any(marker in script_text for marker in js_shell_markers)
