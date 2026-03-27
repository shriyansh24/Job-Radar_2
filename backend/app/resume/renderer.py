"""Resume renderer: IR -> HTML (via Jinja2) -> PDF (via WeasyPrint).

WeasyPrint is an optional dependency. HTML rendering always works;
PDF rendering raises ``RuntimeError`` if WeasyPrint is not installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"

AVAILABLE_TEMPLATES: list[dict[str, str]] = [
    {
        "id": "professional",
        "name": "Professional",
        "description": "Clean, traditional single-column layout with subtle dividers. "
        "Good all-around choice for most industries.",
    },
    {
        "id": "modern",
        "name": "Modern",
        "description": "Two-column layout with a colored sidebar for contact info, "
        "skills, and certifications. Accent color configurable.",
    },
    {
        "id": "minimal",
        "name": "Minimal",
        "description": "Ultra-clean, text-focused single-column design. "
        "Maximum readability and ATS compatibility. Best for traditional industries.",
    },
]

_TEMPLATE_IDS = {t["id"] for t in AVAILABLE_TEMPLATES}


def _to_dict(ir: Any) -> dict[str, Any]:
    """Convert a ResumeIR (or plain dict) to a template-friendly dict."""
    if hasattr(ir, "model_dump"):
        return cast(dict[str, Any], ir.model_dump())
    if isinstance(ir, dict):
        return cast(dict[str, Any], ir)
    raise TypeError(f"Expected ResumeIR or dict, got {type(ir).__name__}")


class ResumeRenderer:
    """Renders a ResumeIR into HTML or PDF using Jinja2 templates."""

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    def get_templates(self) -> list[dict[str, str]]:
        """Return metadata for all available templates."""
        return list(AVAILABLE_TEMPLATES)

    def render_html(self, ir: Any, template_id: str = "professional") -> str:
        """Render a ResumeIR to an HTML string."""
        if template_id not in _TEMPLATE_IDS:
            raise ValueError(
                f"Unknown template '{template_id}'. "
                f"Available: {sorted(_TEMPLATE_IDS)}"
            )
        data = _to_dict(ir)
        template = self.env.get_template(f"{template_id}.html")
        return template.render(resume=data)

    def render_pdf(self, ir: Any, template_id: str = "professional") -> bytes:
        """Render a ResumeIR to PDF bytes. Requires ``weasyprint``."""
        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise RuntimeError(
                "PDF rendering requires the 'weasyprint' package. "
                "Install with: pip install jobradar-v2[pdf]"
            ) from exc

        html_content = self.render_html(ir, template_id)
        return bytes(HTML(string=html_content).write_pdf())

    def render_to_file(
        self, ir: Any, output_path: str, template_id: str = "professional"
    ) -> str:
        """Render PDF and write to *output_path*. Returns the path."""
        pdf_bytes = self.render_pdf(ir, template_id)
        Path(output_path).write_bytes(pdf_bytes)
        return output_path
