"""Tests for AdapterRegistry — maps scraper_name strings to adapter instances and methods."""
import pytest
from app.scraping.execution.adapter_registry import AdapterRegistry, AdapterBinding


def test_register_and_resolve_fetcher():
    reg = AdapterRegistry()

    class FakeFetcher:
        async def fetch(self, url, timeout_s=30):
            return "html"

    adapter = FakeFetcher()
    reg.register_fetcher("cloudscraper", adapter)
    instance, method = reg.resolve("cloudscraper")
    assert instance is adapter
    assert method == adapter.fetch


def test_register_and_resolve_browser():
    reg = AdapterRegistry()

    class FakeBrowser:
        async def render(self, url, timeout_s=60):
            return "html"

    adapter = FakeBrowser()
    reg.register_browser("nodriver", adapter)
    binding = reg.get("nodriver")
    assert binding.is_browser is True
    assert binding.method == "render"


def test_register_ats():
    reg = AdapterRegistry()

    class FakeATS:
        async def fetch_jobs(self, token):
            return []

    adapter = FakeATS()
    reg.register_ats("greenhouse", adapter)
    binding = reg.get("greenhouse")
    assert binding.method == "fetch_jobs"
    assert binding.is_browser is False


def test_unknown_scraper_raises():
    reg = AdapterRegistry()
    with pytest.raises(KeyError):
        reg.get("nonexistent")


def test_dual_mode_scrapling():
    """Same instance registered under two names for dual-mode adapters."""
    reg = AdapterRegistry()

    class FakeDual:
        async def fetch(self, url, timeout_s=30):
            return "html"

        async def render(self, url, timeout_s=60):
            return "html"

    adapter = FakeDual()
    reg.register_fetcher("scrapling_fast", adapter)
    reg.register_browser("scrapling_stealth", adapter)
    inst1, method1 = reg.resolve("scrapling_fast")
    inst2, method2 = reg.resolve("scrapling_stealth")
    assert inst1 is inst2  # same instance
    assert method1 == adapter.fetch
    assert method2 == adapter.render
