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
    def browser_name(self) -> str: ...

    @abstractmethod
    async def render(self, url: str, timeout_s: int = 60,
                     fingerprint: dict | None = None,
                     wait_for_selector: str | None = None) -> BrowserResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None:
        pass
