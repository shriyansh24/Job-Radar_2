"""Maps scraper_name strings from ExecutionPlan Steps to adapter instances and methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


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
        self._bindings[name] = AdapterBinding(instance=adapter, method="fetch", is_browser=False)

    def register_browser(self, name: str, adapter: Any) -> None:
        """Register a headless-browser adapter under the given name."""
        self._bindings[name] = AdapterBinding(instance=adapter, method="render", is_browser=True)

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

    @property
    def registered_names(self) -> list[str]:
        """Return all registered adapter names."""
        return list(self._bindings.keys())


def build_default_registry(settings: Any = None) -> AdapterRegistry:
    """Create and populate an AdapterRegistry with all available adapters.

    This is the single source of truth for adapter registration.
    Used by both the background worker and the API router endpoints.
    """
    registry = AdapterRegistry()

    if settings is None:
        from app.config import settings as default_settings

        settings = default_settings

    # ATS adapters (Tier 0)
    for name, module_path, class_name in [
        ("greenhouse", "app.scraping.scrapers.greenhouse", "GreenhouseScraper"),
        ("lever", "app.scraping.scrapers.lever", "LeverScraper"),
        ("ashby", "app.scraping.scrapers.ashby", "AshbyScraper"),
        ("workday", "app.scraping.scrapers.workday", "WorkdayScraper"),
    ]:
        try:
            import importlib

            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            registry.register_ats(name, cls(settings))
        except Exception as e:
            logger.warning("adapter_skip", name=name, reason=str(e))

    # Fetchers (Tier 1)
    try:
        from app.scraping.execution.cloudscraper_fetcher import CloudscraperFetcher

        registry.register_fetcher("cloudscraper", CloudscraperFetcher())
    except Exception as e:
        logger.warning("adapter_skip", name="cloudscraper", reason=str(e))

    # Scrapling dual-mode (Tier 1 fetch + Tier 2 render)
    try:
        from app.scraping.execution.scrapling_fetcher import ScraplingFetcher

        scrapling = ScraplingFetcher()
        registry.register_fetcher("scrapling_fast", scrapling)
        registry.register_browser("scrapling_stealth", scrapling)
    except Exception as e:
        logger.warning("adapter_skip", name="scrapling", reason=str(e))

    # Browsers (Tier 2-3)
    try:
        from app.scraping.execution.nodriver_browser import NodriverBrowser

        registry.register_browser("nodriver", NodriverBrowser())
    except Exception as e:
        logger.warning("adapter_skip", name="nodriver", reason=str(e))

    try:
        from app.scraping.execution.camoufox_browser import CamoufoxBrowser

        registry.register_browser("camoufox", CamoufoxBrowser())
    except Exception as e:
        logger.warning("adapter_skip", name="camoufox", reason=str(e))

    try:
        from app.scraping.execution.seleniumbase_browser import SeleniumBaseBrowser

        registry.register_browser("seleniumbase", SeleniumBaseBrowser())
    except Exception as e:
        logger.warning("adapter_skip", name="seleniumbase", reason=str(e))

    logger.info("adapter_registry_built", registered=registry.registered_names)
    return registry
