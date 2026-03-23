from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BrowserResult:
    html: str
    status_code: int
    url_final: str
    duration_ms: int
    content_hash: str
    screenshot: bytes | None = None


class BrowserPort(ABC):
    @property
    @abstractmethod
    def browser_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def render(
        self,
        url: str,
        timeout_s: int = 60,
        fingerprint: dict | None = None,
        wait_for_selector: str | None = None,
    ) -> BrowserResult:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError

    async def close(self) -> None:
        return None
