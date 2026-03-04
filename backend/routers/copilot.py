import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.models import Job, UserProfile
from backend.schemas import CopilotRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/copilot", tags=["copilot"])

TOOL_PROMPTS = {
    "coverLetter": """Write a professional cover letter for this job position.
Be specific to the role and company. Use the resume context if provided.

Job Title: {title}
Company: {company_name}
Description: {description}

{resume_context}

Write a compelling, personalized cover letter (3-4 paragraphs).""",

    "interviewPrep": """Prepare interview questions and talking points for this role.

Job Title: {title}
Company: {company_name}
Required Skills: {skills}
Description: {description}

{resume_context}

Provide:
1. 5-7 likely technical interview questions with suggested answers
2. 3-5 behavioral questions to prepare for
3. Key talking points highlighting relevant experience
4. Questions to ask the interviewer""",

    "gapAnalysis": """Analyze the gap between the candidate's resume and this job posting.

Job Title: {title}
Company: {company_name}
Required Skills: {skills_required}
Nice-to-Have Skills: {skills_nice}
Description: {description}

{resume_context}

Provide:
1. Skills and experience that match well
2. Gaps to address
3. Specific actions to strengthen the application
4. An honest assessment of fit (percentage estimate)""",
}


@router.post("")
async def copilot(request: CopilotRequest, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=400, detail="OpenRouter API key not configured")

    # Get the job
    result = await db.execute(select(Job).where(Job.job_id == request.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get resume context
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.id == 1)
    )
    profile = profile_result.scalar_one_or_none()
    resume_context = ""
    if profile and profile.resume_text:
        resume_context = f"Candidate Resume:\n{profile.resume_text[:2000]}"

    # Build prompt
    prompt_template = TOOL_PROMPTS.get(request.tool)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")

    prompt = prompt_template.format(
        title=job.title,
        company_name=job.company_name,
        description=(job.description_clean or "")[:2000],
        skills=", ".join(job.skills_required or []),
        skills_required=", ".join(job.skills_required or []),
        skills_nice=", ".join(job.skills_nice_to_have or []),
        resume_context=resume_context,
    )

    client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "JobRadar",
        },
    )

    async def generate():
        try:
            stream = await client.chat.completions.create(
                model=settings.OPENROUTER_PRIMARY_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career coach and technical recruiter. Provide actionable, specific advice.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Copilot stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
