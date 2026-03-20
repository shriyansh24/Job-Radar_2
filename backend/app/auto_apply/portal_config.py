"""Employer portal configuration loader.

Loads pre-configured ATS mappings from employers.yaml and exposes them via
the PortalConfig class.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

_YAML_PATH = Path(__file__).resolve().parent / "employers.yaml"


class CustomQuestion(BaseModel):
    """A known custom question for a specific employer."""

    key: str
    question: str
    type: str = "short_answer"


class EmployerConfig(BaseModel):
    """Configuration for a single employer's application portal."""

    name: str
    display_name: str
    ats_type: str  # workday, greenhouse, lever, generic
    portal_url: str
    form_mappings: dict[str, str] = Field(default_factory=dict)
    custom_questions: list[CustomQuestion] = Field(default_factory=list)


class PortalConfig:
    """Loads and indexes employer portal configurations from employers.yaml."""

    def __init__(self, yaml_path: Path = _YAML_PATH) -> None:
        self._configs: dict[str, EmployerConfig] = {}
        self._load(yaml_path)

    def _load(self, yaml_path: Path) -> None:
        if not yaml_path.exists():
            logger.warning("portal_config.yaml_not_found", path=str(yaml_path))
            return

        try:
            import yaml
        except ImportError:
            logger.warning("portal_config.pyyaml_not_installed")
            return

        try:
            with yaml_path.open("r", encoding="utf-8") as fh:
                data: dict[str, Any] = yaml.safe_load(fh) or {}
        except Exception as exc:
            logger.error("portal_config.yaml_parse_error", error=str(exc))
            return

        employers_raw: list[dict] = data.get("employers", [])
        for raw in employers_raw:
            try:
                cfg = EmployerConfig(**raw)
                self._configs[self._normalise(cfg.name)] = cfg
                self._configs[self._normalise(cfg.display_name)] = cfg
            except Exception as exc:
                logger.warning("portal_config.skip_entry", name=raw.get("name"), error=str(exc))

        unique = len(set(id(v) for v in self._configs.values()))
        logger.info("portal_config.loaded", count=unique)

    @staticmethod
    def _normalise(name: str) -> str:
        return name.lower().strip().replace(" ", "")

    def get_config(self, company: str) -> EmployerConfig | None:
        return self._configs.get(self._normalise(company))

    def list_employers(self) -> list[str]:
        seen: set[str] = set()
        names: list[str] = []
        for cfg in self._configs.values():
            if cfg.display_name not in seen:
                seen.add(cfg.display_name)
                names.append(cfg.display_name)
        return sorted(names)


_portal_config: PortalConfig | None = None


def get_portal_config() -> PortalConfig:
    """Return the module-level PortalConfig singleton."""
    global _portal_config
    if _portal_config is None:
        _portal_config = PortalConfig()
    return _portal_config
