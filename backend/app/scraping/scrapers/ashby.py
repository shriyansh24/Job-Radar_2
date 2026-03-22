from __future__ import annotations

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class AshbyScraper(BaseScraper):
    """Ashby ATS job boards via their GraphQL API."""

    GRAPHQL_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"
    QUERY = (
        "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {"
        " jobBoard: jobBoardWithTeams("
        "organizationHostedJobsPageName: $organizationHostedJobsPageName) {"
        " teams { ... on JobBoardTeam { name jobs {"
        " id title employmentType locationName isRemote } } } } }"
    )

    @property
    def source_name(self) -> str:
        return "ashby"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Fetch from Ashby job board API. query = organization slug."""
        payload = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {"organizationHostedJobsPageName": query},
            "query": self.QUERY,
        }

        resp = await self.client.post(self.GRAPHQL_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            logger.warning("ashby.invalid_response_shape", query=query)
            return []
        if data.get("errors"):
            logger.warning("ashby.graphql_errors", query=query)
            return []

        jobs: list[ScrapedJob] = []
        board_data = data.get("data", {})
        if not isinstance(board_data, dict):
            logger.warning("ashby.invalid_data_payload", query=query)
            return []
        board = board_data.get("jobBoard", {})
        if not isinstance(board, dict):
            logger.warning("ashby.invalid_board_payload", query=query)
            return []
        for team in board.get("teams", []):
            if not isinstance(team, dict):
                continue
            for item in team.get("jobs", []):
                if not isinstance(item, dict):
                    continue
                jobs.append(
                    ScrapedJob(
                        title=item["title"],
                        company_name=query,
                        source=self.source_name,
                        source_url=f"https://jobs.ashbyhq.com/{query}/{item['id']}",
                        location=item.get("locationName", ""),
                        remote_type=(
                            "remote"
                            if item.get("isRemote")
                            else self._normalize_remote_type(item.get("locationName"))
                        ),
                        job_type=item.get("employmentType"),
                    )
                )
        return jobs[:limit]

    async def health_check(self) -> bool:
        try:
            payload = {
                "operationName": "ApiJobBoardWithTeams",
                "variables": {"organizationHostedJobsPageName": "__health__"},
                "query": self.QUERY,
            }
            resp = await self.client.post(self.GRAPHQL_URL, json=payload)
            return resp.status_code == 200
        except Exception:
            return False
