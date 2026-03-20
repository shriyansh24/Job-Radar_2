"""Maps scraper_name strings from ExecutionPlan Steps to adapter instances and methods."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class AdapterBinding:
    """Holds an adapter instance plus metadata about how to call it."""

    instance: Any
    method: str  # "fetch", "render", or "fetch_jobs"
    is_browser: bool = False


class AdapterRegistry:
    """Registry mapping scraper_name strings to adapter instances and their callable methods.

    Supports three adapter categories:
    - Fetchers (HTTP-based, method="fetch")
    - Browsers (headless browser, method="render")
    - ATS adapters (API-based, method="fetch_jobs")

    The same adapter instance can be registered under multiple names to support
    dual-mode adapters (e.g. scrapling registered as both a fetcher and browser).
    """

    def __init__(self) -> None:
        self._bindings: dict[str, AdapterBinding] = {}

    def register_fetcher(self, name: str, adapter: Any) -> None:
        """Register an HTTP fetcher adapter under the given name."""
        self._bindings[name] = AdapterBinding(
            instance=adapter, method="fetch", is_browser=False
        )

    def register_browser(self, name: str, adapter: Any) -> None:
        """Register a headless-browser adapter under the given name."""
        self._bindings[name] = AdapterBinding(
            instance=adapter, method="render", is_browser=True
        )

    def register_ats(self, name: str, adapter: Any) -> None:
        """Register an ATS (Applicant Tracking System) API adapter under the given name."""
        self._bindings[name] = AdapterBinding(
            instance=adapter, method="fetch_jobs", is_browser=False
        )

    def get(self, scraper_name: str) -> AdapterBinding:
        """Look up the binding for a scraper_name. Raises KeyError if not registered."""
        if scraper_name not in self._bindings:
            raise KeyError(f"No adapter registered for '{scraper_name}'")
        return self._bindings[scraper_name]

    def resolve(self, scraper_name: str) -> tuple[Any, Callable]:
        """Return (adapter_instance, bound_method) for a scraper_name.

        This is the primary entry point for the execution engine: given a
        scraper_name from an ExecutionPlan Step, get the object and the
        callable to invoke.
        """
        binding = self.get(scraper_name)
        return binding.instance, getattr(binding.instance, binding.method)
