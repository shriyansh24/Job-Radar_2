"""Copilot prompt templates and context-building helpers."""

from __future__ import annotations

COPILOT_SYSTEM_PROMPT = (
    "You are JobRadar AI, a helpful career assistant. You help users with:\n"
    "- Understanding job descriptions and requirements\n"
    "- Preparing for interviews\n"
    "- Improving their resumes and cover letters\n"
    "- Salary negotiation advice\n"
    "- General career guidance\n\n"
    "Be concise, practical, and encouraging. When the user provides job or "
    "resume context, tailor your advice specifically to their situation."
)


def build_context_messages(context: dict | None) -> list[dict[str, str]]:
    """Turn an optional context dict into LLM system messages.

    Returns a list of zero or one message dicts ready to be inserted into
    the messages list between the system prompt and the user message.
    """
    if not context:
        return []

    parts: list[str] = []
    if context.get("job_title"):
        parts.append(f"Job title: {context['job_title']}")
    if context.get("company_name"):
        parts.append(f"Company: {context['company_name']}")
    if context.get("job_description"):
        desc = context["job_description"][:2000]
        parts.append(f"Job description:\n{desc}")
    if context.get("resume_text"):
        resume = context["resume_text"][:2000]
        parts.append(f"User's resume:\n{resume}")

    if not parts:
        return []

    return [{"role": "system", "content": "Context:\n" + "\n\n".join(parts)}]
