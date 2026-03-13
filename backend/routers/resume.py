"""Resume REST API — upload, list, preview, delete, update versions."""
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import ResumeVersion
from backend.schemas import ResumeVersionResponse
from backend.resume.document_manager import (
    ingest_resume,
    delete_resume as delete_resume_file,
    get_resume_by_id,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["resume"])


@router.get("/versions", response_model=list[ResumeVersionResponse])
async def list_versions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResumeVersion).order_by(ResumeVersion.created_at.desc())
    )
    versions = result.scalars().all()
    return [
        ResumeVersionResponse(
            id=v.id,
            filename=v.filename,
            format=v.format,
            version_label=v.version_label,
            is_default=v.is_default,
            parsed_text_preview=(v.parsed_text or "")[:200],
            created_at=v.created_at.isoformat() if v.created_at else "",
        )
        for v in versions
    ]


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    version_label: str = Query(default="v1"),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()

    try:
        doc = ingest_resume(content, file.filename, version_label=version_label)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check if this is the first resume (auto-set as default)
    existing = await db.execute(select(ResumeVersion).limit(1))
    is_first = existing.scalar_one_or_none() is None

    # Create DB record
    rv = ResumeVersion(
        id=doc.id,
        filename=doc.filename,
        format=doc.format,
        file_path=doc.file_path,
        parsed_text=doc.parsed_text,
        parsed_structured=doc.parsed_structured,
        version_label=doc.version_label,
        is_default=is_first,
    )
    db.add(rv)
    await db.commit()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "format": doc.format,
        "version_label": doc.version_label,
        "is_default": is_first,
        "text_length": len(doc.parsed_text),
        "sections": list(doc.parsed_structured.keys()),
    }


@router.get("/versions/{version_id}")
async def get_version(version_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(status_code=404, detail="Resume version not found")

    return {
        "id": rv.id,
        "filename": rv.filename,
        "format": rv.format,
        "version_label": rv.version_label,
        "is_default": rv.is_default,
        "parsed_text": rv.parsed_text,
        "parsed_structured": rv.parsed_structured,
        "created_at": rv.created_at.isoformat() if rv.created_at else "",
    }


@router.get("/versions/{version_id}/preview")
async def preview_version(version_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(status_code=404, detail="Resume version not found")

    return {
        "id": rv.id,
        "filename": rv.filename,
        "preview": (rv.parsed_text or "")[:500],
        "sections": rv.parsed_structured or {},
    }


@router.delete("/versions/{version_id}")
async def delete_version(version_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(status_code=404, detail="Resume version not found")

    # Delete file from disk
    delete_resume_file(rv.id, rv.format)

    # Delete DB record
    await db.delete(rv)
    await db.commit()

    return {"deleted": version_id}


@router.patch("/versions/{version_id}")
async def update_version(
    version_id: str,
    version_label: str | None = None,
    is_default: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(status_code=404, detail="Resume version not found")

    if version_label is not None:
        rv.version_label = version_label

    if is_default is True:
        # Unset other defaults
        all_versions = await db.execute(select(ResumeVersion))
        for v in all_versions.scalars().all():
            v.is_default = v.id == version_id

    await db.commit()

    return {
        "id": rv.id,
        "version_label": rv.version_label,
        "is_default": rv.is_default,
    }
