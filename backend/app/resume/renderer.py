"""PDF renderer for resumes using Jinja2 templates and WeasyPrint.

Takes a ResumeIR dict and produces PDF bytes via HTML/CSS rendering.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from jinja2 import Environment, FileSystemLoader

logger = structlog.get_logger()

TEMPLATE_DIR = Path(__file__).parent / "templates"

_AVAILABLE_TEMPLATES = [
    {
        "id": "professional",
        "name": "Professional",
        "description": "Clean, traditional single-column layout",
    },
]


class ResumeRenderer:
    """Renders ResumeIR dicts into HTML and PDF."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    def get_templates(self) -> list[dict[str, str]]:
        """Return metadata about available resume templates."""
        return list(_AVAILABLE_TEMPLATES)

    def render_html(self, ir: dict[str, Any], template_id: str = "professional") -> str:
        """Render a ResumeIR dict to an HTML string."""
        template = self._env.get_template(f"{template_id}.html")
        # Wrap the dict in a namespace so templates access resume.contact etc.
        return template.render(resume=_wrap_ir(ir))

    def render_pdf(self, ir: dict[str, Any], template_id: str = "professional") -> bytes:
        """Render a ResumeIR dict to PDF bytes."""
        from weasyprint import HTML

        html_content = self.render_html(ir, template_id)
        logger.info("renderer.render_pdf", template=template_id)
        return HTML(string=html_content).write_pdf()  # type: ignore[return-value]

    def render_to_file(
        self, ir: dict[str, Any], output_path: str, template_id: str = "professional"
    ) -> str:
        """Render a ResumeIR dict to a PDF file on disk."""
        pdf_bytes = self.render_pdf(ir, template_id)
        Path(output_path).write_bytes(pdf_bytes)
        return output_path


class _DictWrapper:
    """Allows dict keys to be accessed as attributes for Jinja2 templates."""

    def __init__(self, data: dict[str, Any] | None) -> None:
        self._data = data or {}

    def __getattr__(self, name: str) -> Any:
        val = self._data.get(name)
        if isinstance(val, dict):
            return _DictWrapper(val)
        if isinstance(val, list):
            return [_DictWrapper(v) if isinstance(v, dict) else v for v in val]
        return val

    def __bool__(self) -> bool:
        return bool(self._data)

    def __str__(self) -> str:
        return str(self._data)

    def items(self) -> Any:
        return self._data.items()

    def __iter__(self) -> Any:
        return iter(self._data)


def _wrap_ir(ir: dict[str, Any]) -> _DictWrapper:
    """Wrap an IR dict so Jinja2 templates can use dot notation."""
    return _DictWrapper(ir)
