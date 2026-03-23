from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auto_apply.form_learning import FormLearningService
from app.auto_apply.schemas import (
    ApplySingleRequest,
    AutoApplyProfileCreate,
    AutoApplyProfileResponse,
    AutoApplyProfileUpdate,
    AutoApplyStatsResponse,
    FieldMappingRuleResponse,
    RuleCreate,
    RuleResponse,
    RuleUpdate,
    RunResult,
)
from app.auto_apply.service import AutoApplyService
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/auto-apply", tags=["auto_apply"])


@router.get("/profiles", response_model=list[AutoApplyProfileResponse])
async def list_profiles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AutoApplyProfileResponse]:
    svc = AutoApplyService(db)
    items = await svc.list_profiles(user.id)
    return [AutoApplyProfileResponse.model_validate(p) for p in items]


@router.post("/profiles", response_model=AutoApplyProfileResponse, status_code=201)
async def create_profile(
    data: AutoApplyProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutoApplyProfileResponse:
    svc = AutoApplyService(db)
    p = await svc.create_profile(data, user.id)
    return AutoApplyProfileResponse.model_validate(p)


@router.patch("/profiles/{profile_id}", response_model=AutoApplyProfileResponse)
async def update_profile(
    profile_id: uuid.UUID,
    data: AutoApplyProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutoApplyProfileResponse:
    svc = AutoApplyService(db)
    p = await svc.update_profile(profile_id, data, user.id)
    return AutoApplyProfileResponse.model_validate(p)


@router.get("/rules", response_model=list[RuleResponse])
async def list_rules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RuleResponse]:
    svc = AutoApplyService(db)
    items = await svc.list_rules(user.id)
    return [RuleResponse.model_validate(r) for r in items]


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(
    data: RuleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RuleResponse:
    svc = AutoApplyService(db)
    r = await svc.create_rule(data, user.id)
    return RuleResponse.model_validate(r)


@router.patch("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    data: RuleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RuleResponse:
    svc = AutoApplyService(db)
    r = await svc.update_rule(rule_id, data, user.id)
    return RuleResponse.model_validate(r)


@router.delete("/rules/{rule_id}", status_code=204, response_model=None)
async def delete_rule(
    rule_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = AutoApplyService(db)
    await svc.delete_rule(rule_id, user.id)


@router.get("/stats", response_model=AutoApplyStatsResponse)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutoApplyStatsResponse:
    svc = AutoApplyService(db)
    result = await svc.get_stats(user.id)
    return AutoApplyStatsResponse(**result)


@router.get("/runs", response_model=list[RunResult])
async def list_runs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RunResult]:
    svc = AutoApplyService(db)
    items = await svc.list_runs(user.id)
    return [RunResult.model_validate(r) for r in items]


@router.post("/run")
async def trigger_run(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AutoApplyService(db)
    return await svc.trigger_run(user.id)


@router.post("/apply-single")
async def apply_single(
    data: ApplySingleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AutoApplyService(db)
    return await svc.apply_single(data.job_id, user.id)


@router.post("/pause")
async def pause_auto_apply(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AutoApplyService(db)
    return await svc.pause(user.id)


# -- Form learning (admin) endpoints -----------------------------------


@router.get("/learned-mappings", response_model=list[FieldMappingRuleResponse])
async def list_learned_mappings(
    limit: int = 100,
    offset: int = 0,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FieldMappingRuleResponse]:
    svc = FormLearningService(db)
    items = await svc.list_mappings(limit=limit, offset=offset)
    return [FieldMappingRuleResponse.model_validate(m) for m in items]


@router.delete("/learned-mappings/{rule_id}", status_code=204, response_model=None)
async def delete_learned_mapping(
    rule_id: uuid.UUID,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = FormLearningService(db)
    deleted = await svc.delete_mapping(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mapping rule not found")
    await db.commit()
