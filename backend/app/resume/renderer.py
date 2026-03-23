"""HTML/PDF renderer for resume templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from jinja2 import Environment, FileSystemLoader

from app.resume.ir_schema import ResumeIR

logger = structlog.get_logger()

TEMPLATE_DIR = Path(__file__).parent / "templates"
_AVAILABLE_TEMPLATES = [
    {
        "id": "professional",
        "name": "Professional",
        "description": "Balanced single-column layout with compact skill tags.",
    },
    {
        "id": "modern",
        "name": "Modern",
        "description": "Two-column layout with a bold accent sidebar.",
    },
    {
        "id": "minimal",
        "name": "Minimal",
        "description": "Monochrome editorial layout with restrained styling.",
    },
]


class ResumeRenderer:
    """Render ResumeIR payloads into HTML or PDF using Jinja templates."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    def get_templates(self) -> list[dict[str, str]]:
        return list(_AVAILABLE_TEMPLATES)

    def render_html(
        self,
        ir: ResumeIR | dict[str, Any],
        template_id: str = "professional",
    ) -> str:
        template_ids = {template["id"] for template in _AVAILABLE_TEMPLATES}
        if template_id not in template_ids:
            raise ValueError(f"Unknown template: {template_id}")

        if isinstance(ir, ResumeIR):
            payload = ir.model_dump()
        elif isinstance(ir, dict):
            payload = ir
        else:
            raise TypeError("Expected ResumeIR or dict")

        template = self._env.get_template(f"{template_id}.html")
        return template.render(resume=_DictWrapper(payload))

    def render_pdf(
        self,
        ir: ResumeIR | dict[str, Any],
        template_id: str = "professional",
    ) -> bytes:
        from weasyprint import HTML

        html_content = self.render_html(ir, template_id)
        logger.info("resume_renderer.render_pdf", template=template_id)
        return HTML(string=html_content).write_pdf()  # type: ignore[return-value]

    def render_to_file(
        self,
        ir: ResumeIR | dict[str, Any],
        output_path: str,
        template_id: str = "professional",
    ) -> str:
        pdf_bytes = self.render_pdf(ir, template_id)
        Path(output_path).write_bytes(pdf_bytes)
        return output_path


class _DictWrapper:
    """Allow dot-notation access for dict-backed Jinja templates."""

    def __init__(self, data: dict[str, Any] | None) -> None:
        self._data = data or {}

    def __getattr__(self, name: str) -> Any:
        value = self._data.get(name)
        if isinstance(value, dict):
            return _DictWrapper(value)
        if isinstance(value, list):
            return [_DictWrapper(item) if isinstance(item, dict) else item for item in value]
        return value

    def __bool__(self) -> bool:
        return bool(self._data)

    def items(self) -> Any:
        return self._data.items()


