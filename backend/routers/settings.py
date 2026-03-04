import logging
import os
from datetime import datetime
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.models import UserProfile
from backend.schemas import SettingsResponse, SettingsUpdate, SavedSearchCreate, SavedSearchResponse
from backend.models import SavedSearch

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["settings"])


async def _get_or_create_profile(db: AsyncSession) -> UserProfile:
    result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(id=1)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("/settings", response_model=SettingsResponse)
async def get_settings_endpoint(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    profile = await _get_or_create_profile(db)

    return SettingsResponse(
        serpapi_key_set=bool(settings.SERPAPI_KEY),
        theirstack_key_set=bool(settings.THEIRSTACK_KEY),
        apify_key_set=bool(settings.APIFY_KEY),
        openrouter_key_set=bool(settings.OPENROUTER_API_KEY),
        openrouter_primary_model=settings.OPENROUTER_PRIMARY_MODEL,
        openrouter_fallback_model=settings.OPENROUTER_FALLBACK_MODEL,
        default_queries=profile.default_queries or [],
        default_locations=profile.default_locations or [],
        company_watchlist=profile.company_watchlist or [],
        resume_filename=profile.resume_filename,
        resume_uploaded_at=profile.resume_uploaded_at,
    )


@router.post("/settings", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    profile = await _get_or_create_profile(db)

    # Update .env file for API keys
    env_updates = {}
    if body.serpapi_key is not None:
        env_updates["SERPAPI_KEY"] = body.serpapi_key
    if body.theirstack_key is not None:
        env_updates["THEIRSTACK_KEY"] = body.theirstack_key
    if body.apify_key is not None:
        env_updates["APIFY_KEY"] = body.apify_key
    if body.openrouter_api_key is not None:
        env_updates["OPENROUTER_API_KEY"] = body.openrouter_api_key
    if body.openrouter_primary_model is not None:
        env_updates["OPENROUTER_PRIMARY_MODEL"] = body.openrouter_primary_model
    if body.openrouter_fallback_model is not None:
        env_updates["OPENROUTER_FALLBACK_MODEL"] = body.openrouter_fallback_model

    if env_updates:
        await _update_env_file(env_updates)
        # Clear settings cache
        get_settings.cache_clear()

    # Update profile
    if body.default_queries is not None:
        profile.default_queries = body.default_queries
    if body.default_locations is not None:
        profile.default_locations = body.default_locations
    if body.company_watchlist is not None:
        profile.company_watchlist = body.company_watchlist

    await db.commit()

    return await get_settings_endpoint(db)


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "txt"):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    # Parse text from file
    if ext == "txt":
        resume_text = content.decode("utf-8", errors="ignore")
    else:
        try:
            import io
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
                resume_text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            except ImportError:
                resume_text = content.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            raise HTTPException(status_code=400, detail="Failed to parse PDF")

    # Save to profile
    profile = await _get_or_create_profile(db)
    profile.resume_filename = file.filename
    profile.resume_text = resume_text
    profile.resume_uploaded_at = datetime.utcnow()
    await db.commit()

    # Trigger re-embedding
    from backend.enrichment.embedding import load_resume_embedding
    await load_resume_embedding()

    return {
        "filename": file.filename,
        "text_length": len(resume_text),
        "uploaded_at": profile.resume_uploaded_at.isoformat(),
    }


# --- Saved Searches ---

@router.get("/saved-searches", response_model=list[SavedSearchResponse])
async def list_saved_searches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SavedSearch).order_by(SavedSearch.created_at.desc())
    )
    return [SavedSearchResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/saved-searches", response_model=SavedSearchResponse)
async def create_saved_search(
    body: SavedSearchCreate, db: AsyncSession = Depends(get_db)
):
    search = SavedSearch(
        name=body.name,
        query_params=body.query_params,
        alert_enabled=body.alert_enabled,
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)
    return SavedSearchResponse.model_validate(search)


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SavedSearch).where(SavedSearch.id == search_id)
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    await db.delete(search)
    await db.commit()
    return {"status": "deleted"}


async def _update_env_file(updates: dict):
    env_path = ".env"
    lines = []

    if os.path.exists(env_path):
        async with aiofiles.open(env_path, "r") as f:
            lines = (await f.read()).splitlines()

    updated_keys = set()
    new_lines = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line else None
        if key and key in updates:
            new_lines.append(f'{key}="{updates[key]}"')
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f'{key}="{value}"')

    async with aiofiles.open(env_path, "w") as f:
        await f.write("\n".join(new_lines) + "\n")
