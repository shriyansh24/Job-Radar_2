from __future__ import annotations


class ATSDetector:
    """Detect which ATS platform a job application uses."""

    ATS_PATTERNS: dict[str, list[str]] = {
        "greenhouse": ["greenhouse.io", "boards.greenhouse.io"],
        "lever": ["lever.co", "jobs.lever.co"],
        "workday": ["myworkdayjobs.com", "wd5.myworkdayjobs", "workday.com"],
        "ashby": ["ashbyhq.com", "jobs.ashbyhq.com"],
        "icims": ["icims.com", "careers-"],
        "taleo": ["taleo.net", "oracle.com/taleo"],
        "bamboohr": ["bamboohr.com"],
        "jazz": ["applytojob.com", "jazzhr.com"],
        "smartrecruiters": ["smartrecruiters.com"],
        "jobvite": ["jobvite.com"],
    }

    @classmethod
    def detect(cls, url: str) -> str | None:
        """Return ATS provider name or None."""
        url_lower = url.lower()
        for ats, patterns in cls.ATS_PATTERNS.items():
            if any(p in url_lower for p in patterns):
                return ats
        return None

    @classmethod
    async def detect_from_page(cls, page: object) -> str | None:
        """Detect ATS from page content (Playwright page object)."""
        url: str = getattr(page, "url", "").lower()
        result = cls.detect(url)
        if result:
            return result

        # Check page source for ATS signatures
        content: str = await page.content()  # type: ignore[union-attr]
        content_lower = content.lower()
        if "greenhouse" in content_lower:
            return "greenhouse"
        if "lever" in content_lower and "lever.co" in content_lower:
            return "lever"
        if "workday" in content_lower:
            return "workday"
        return None
