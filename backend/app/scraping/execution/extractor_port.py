from __future__ import annotations

from abc import ABC, abstractmethod

from app.scraping.port import ScrapedJob


class ExtractorPort(ABC):
    @abstractmethod
    async def extract_jobs(self, html: str, url: str) -> list[ScrapedJob]:
        raise NotImplementedError

    @abstractmethod
    async def to_markdown(self, html: str) -> str:
        raise NotImplementedError
