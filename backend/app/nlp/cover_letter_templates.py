"""Cover letter template library defining structure, tone, and flow for each template type.

Ported from v1 — provides template definitions for formal, startup,
career-change, and technical cover letter styles.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_TEMPLATES: frozenset[str] = frozenset({"formal", "startup", "career-change", "technical"})


def _text(*parts: str) -> str:
    return "".join(parts)


@dataclass(frozen=True)
class CoverLetterTemplate:
    """Defines a complete cover letter template with structure and tone guidance."""

    name: str
    display_name: str
    greeting_style: str
    paragraph_flow: tuple[str, ...]
    closing_style: str
    tone_guidance: str
    prompt_instructions: str


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

FORMAL_TEMPLATE = CoverLetterTemplate(
    name="formal",
    display_name="Formal / Corporate",
    greeting_style=_text(
        "Use a formal salutation addressing the hiring manager by name if known "
        "(e.g. 'Dear Ms. Smith,') or 'Dear Hiring Manager,' if name is unavailable. "
        "Never use casual greetings such as 'Hi' or 'Hello'.",
    ),
    paragraph_flow=(
        _text(
            "Opening paragraph: State the specific role you are applying for, "
            "where you found the listing, and a concise one-sentence summary of your "
            "strongest qualification for the position.",
        ),
        _text(
            "Body paragraph 1: Describe your most relevant professional experience and "
            "accomplishments with quantified results (percentages, dollar amounts, team sizes). "
            "Tie each achievement directly to a stated job requirement.",
        ),
        _text(
            "Body paragraph 2: Highlight two or three key skills or competencies that align "
            "with the company's stated needs. Reference the company's mission or recent "
            "initiatives to show genuine research.",
        ),
        _text(
            "Closing paragraph: Reiterate your enthusiasm, request a specific next step "
            "(interview or call), and thank the reader for their time.",
        ),
    ),
    closing_style=_text(
        "Close with a formal sign-off such as 'Sincerely,' or 'Respectfully,' "
        "followed by the candidate's full name.",
    ),
    tone_guidance=_text(
        "Maintain a polished, authoritative, and respectful tone throughout. "
        "Use precise business language. Avoid contractions, colloquialisms, and "
        "first-person overuse. Every sentence should be purposeful and demonstrate "
        "professionalism consistent with a traditional corporate environment.",
    ),
    prompt_instructions=_text(
        "Write in a formal, corporate tone. Use complete sentences and precise business "
        "language. Structure: formal greeting, strong opening hook, two substantive body "
        "paragraphs with quantified achievements, confident closing with a call to action. "
        "Avoid contractions. Reference the company's name and mission specifically.",
    ),
)

STARTUP_TEMPLATE = CoverLetterTemplate(
    name="startup",
    display_name="Startup / Casual",
    greeting_style=_text(
        "Use a warm, direct greeting. Address the hiring manager by first name if known "
        "(e.g. 'Hi Alex,') or 'Hi there,' if unknown. Convey approachability from the first word.",
    ),
    paragraph_flow=(
        _text(
            "Opening paragraph: Lead with genuine enthusiasm for the company's mission or "
            "a specific product/feature that resonates with you. Briefly introduce yourself "
            "and why you are excited about this particular role.",
        ),
        _text(
            "Body paragraph 1: Tell a short story about a problem you solved or a project "
            "you owned end-to-end. Focus on your impact, speed of execution, and ownership "
            "mindset. Use concrete results.",
        ),
        _text(
            "Body paragraph 2: Highlight your passion for the startup's space, your ability "
            "to wear multiple hats, and two or three skills that directly match the role. "
            "Show cultural fit -- curiosity, collaboration, bias for action.",
        ),
        _text(
            "Closing paragraph: Express eagerness to contribute and grow with the team. "
            "Keep it upbeat and forward-looking. Invite a conversation.",
        ),
    ),
    closing_style=_text(
        "Close with an energetic, friendly sign-off such as 'Excited to connect,' "
        "or 'Looking forward to chatting,' followed by the candidate's first name.",
    ),
    tone_guidance=_text(
        "Be authentic, enthusiastic, and direct. Contractions are encouraged. "
        "Show personality and passion. Avoid corporate jargon -- speak like a person, "
        "not a press release. Demonstrate a growth mindset and excitement about the "
        "company's vision. Keep it conversational but still focused and professional.",
    ),
    prompt_instructions=_text(
        "Write in a casual, passion-driven startup tone. Use contractions and natural "
        "language. Structure: warm greeting, enthusiastic opening about the company's "
        "mission, an impactful story from experience, a cultural-fit paragraph, and an "
        "upbeat closing. Show genuine excitement and a bias for action.",
    ),
)

CAREER_CHANGE_TEMPLATE = CoverLetterTemplate(
    name="career-change",
    display_name="Career Change",
    greeting_style=_text(
        "Use a professional yet personable greeting. 'Dear [Name],' or "
        "'Dear Hiring Team,' works well. Set a confident, positive tone immediately.",
    ),
    paragraph_flow=(
        _text(
            "Opening paragraph: Directly and confidently acknowledge the career transition. "
            "Frame it as intentional and motivated. State the specific role you are targeting "
            "and express clear enthusiasm for entering this new field.",
        ),
        _text(
            "Body paragraph 1 (Transferable Skills Bridge): Identify two or three concrete "
            "skills or experiences from your previous career that directly apply to this new "
            "role. Use specific examples with outcomes. Draw explicit connections so the "
            "hiring manager doesn't have to make the leap themselves.",
        ),
        _text(
            "Body paragraph 2 (Demonstrated Commitment): Show the steps you have taken to "
            "transition -- courses, certifications, side projects, volunteer work, or "
            "freelance experience in the new field. Emphasise learning agility and motivation.",
        ),
        _text(
            "Closing paragraph: Reaffirm your commitment to the new direction and your "
            "unique perspective as someone bringing cross-industry insights. Request an "
            "interview and thank the reader.",
        ),
    ),
    closing_style=_text(
        "Close with a confident, forward-looking sign-off such as 'With enthusiasm,' "
        "or 'Looking forward to the opportunity,' followed by the candidate's full name.",
    ),
    tone_guidance=_text(
        "Project confidence and intentionality. Never apologise for the career change "
        "or frame past experience as a deficiency. Instead, position diverse background "
        "as a competitive advantage. Be honest and direct about the transition while "
        "staying optimistic and results-focused. Avoid being defensive.",
    ),
    prompt_instructions=_text(
        "Write for a career changer -- emphasise transferable skills and reframe past "
        "experience as an asset. Structure: confident opening acknowledging the transition, "
        "a paragraph bridging transferable skills to the new role with specific examples, "
        "a paragraph demonstrating commitment to the new field (courses/projects), and a "
        "strong closing. Never apologise for the career change; position it as a strength.",
    ),
)

TECHNICAL_TEMPLATE = CoverLetterTemplate(
    name="technical",
    display_name="Technical",
    greeting_style=_text(
        "Use a professional greeting. 'Dear [Name],' or 'Dear Engineering Team,' "
        "is appropriate. Get to the technical substance quickly.",
    ),
    paragraph_flow=(
        _text(
            "Opening paragraph: Lead with a specific, impressive technical achievement or "
            "metric that is directly relevant to the role. State the position you are "
            "applying for and why your technical background makes you a strong fit.",
        ),
        _text(
            "Body paragraph 1 (Technical Depth): Detail the most relevant technical project "
            "or system you built or improved. Cover the problem, your technical approach, "
            "the tools and languages used, and measurable outcomes (performance gains, "
            "scale, cost reduction, reliability improvements).",
        ),
        _text(
            "Body paragraph 2 (Skill Alignment): Map your core technical competencies to "
            "the job's required skills. Reference specific technologies, frameworks, "
            "or methodologies mentioned in the job description. Show breadth and depth.",
        ),
        _text(
            "Closing paragraph: Express confidence in contributing technically from day one. "
            "Mention openness to a technical discussion or coding exercise. "
            "Thank the reader briefly.",
        ),
    ),
    closing_style=_text(
        "Close with a professional sign-off such as 'Best regards,' or 'Thank you,' "
        "followed by the candidate's full name and optionally a link to GitHub or portfolio.",
    ),
    tone_guidance=_text(
        "Be precise, concrete, and metrics-driven. Use correct industry and domain "
        "terminology. Lead with technical accomplishments, not soft skills. "
        "Avoid vague statements -- every claim should be backed by a specific example "
        "or number. Demonstrate deep technical expertise and an engineering mindset. "
        "Keep prose tight and efficient; engineers value clarity over flourish.",
    ),
    prompt_instructions=_text(
        "Write with a focus on technical achievements and concrete metrics. Use industry "
        "terminology accurately. Structure: strong opening with a headline technical "
        "achievement, a deep-dive paragraph on a relevant project with tech stack and "
        "measurable outcomes, a skills-alignment paragraph mapping competencies to job "
        "requirements, and a concise closing. Lead with numbers and impact.",
    ),
)

# ---------------------------------------------------------------------------
# Lookup registry
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, CoverLetterTemplate] = {
    "formal": FORMAL_TEMPLATE,
    "startup": STARTUP_TEMPLATE,
    "career-change": CAREER_CHANGE_TEMPLATE,
    "technical": TECHNICAL_TEMPLATE,
}


def get_template(name: str) -> CoverLetterTemplate:
    """Return a CoverLetterTemplate by name.

    Args:
        name: Template name -- one of 'formal', 'startup', 'career-change', 'technical'.

    Returns:
        The matching CoverLetterTemplate.

    Raises:
        ValueError: If the template name is not recognised.
    """
    template = TEMPLATE_REGISTRY.get(name)
    if template is None:
        raise ValueError(f"Unknown template {name!r}. Valid templates: {sorted(VALID_TEMPLATES)}")
    return template


def build_template_prompt_section(template: CoverLetterTemplate) -> str:
    """Render a template's guidance into a formatted string for inclusion in an LLM prompt.

    Args:
        template: A CoverLetterTemplate instance.

    Returns:
        A multi-line string describing the template structure and tone to the LLM.
    """
    flow_items = "\n".join(f"  {i + 1}. {step}" for i, step in enumerate(template.paragraph_flow))
    return (
        f"TEMPLATE: {template.display_name}\n\n"
        f"GREETING STYLE:\n{template.greeting_style}\n\n"
        f"PARAGRAPH FLOW:\n{flow_items}\n\n"
        f"CLOSING STYLE:\n{template.closing_style}\n\n"
        f"TONE GUIDANCE:\n{template.tone_guidance}\n\n"
        f"WRITING INSTRUCTIONS:\n{template.prompt_instructions}"
    )
