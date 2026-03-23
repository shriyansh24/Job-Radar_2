from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class FetchResult:
    html: str
    status_code: int
    headers: dict[str, str]
    url_final: str
    duration_ms: int
    content_hash: str


class FetcherPort(ABC):
    @property
    @abstractmethod
    def fetcher_name(self) -> str: ...

    @abstractmethod
    async def fetch(
        self, url: str, timeout_s: int = 30, user_agent: str | None = None
    ) -> FetchResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None:
        pass
