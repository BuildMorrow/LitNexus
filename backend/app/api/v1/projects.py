from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned_project
from app.core.database import get_db
from app.models.project import ResearchProject
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, SetupAssistRequest
from app.services.setup_agents import (
    CriteriaGenerationResult,
    PICOQueryResult,
    ScopeAnalysisResult,
    run_criteria_generator,
    run_pico_query_generator,
    run_scope_optimizer,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchProject)
        .where(ResearchProject.owner_id == current_user.id)
        .order_by(ResearchProject.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = ResearchProject(
        owner_id=current_user.id,
        title=payload.title,
        domain=payload.domain,
        research_question=payload.research_question,
        pico_framework=payload.pico_framework,
        inclusion_criteria=payload.inclusion_criteria,
        exclusion_criteria=payload.exclusion_criteria,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project: ResearchProject = Depends(get_owned_project)):
    return project


@router.post("/assist/scope-optimizer", response_model=ScopeAnalysisResult)
async def assist_scope_optimizer(
    payload: SetupAssistRequest,
    _current_user: User = Depends(get_current_user),
):
    """Evaluate topic scope width and propose sharpened academic research questions."""
    try:
        return await run_scope_optimizer(idea=payload.idea, research_field=payload.domain)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Scope Optimizer agent failed: {exc}"
        ) from exc


@router.post("/assist/criteria-generator", response_model=CriteriaGenerationResult)
async def assist_criteria_generator(
    payload: SetupAssistRequest,
    _current_user: User = Depends(get_current_user),
):
    """Generate PRISMA 2020 inclusion and exclusion criteria for the research topic."""
    try:
        return await run_criteria_generator(idea=payload.idea, research_field=payload.domain)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Criteria Generator agent failed: {exc}"
        ) from exc


@router.post("/assist/pico-query", response_model=PICOQueryResult)
async def assist_pico_query(
    payload: SetupAssistRequest,
    _current_user: User = Depends(get_current_user),
):
    """Extract English PICO structure and Boolean search query."""
    try:
        return await run_pico_query_generator(
            idea=payload.idea,
            research_field=payload.domain,
            inclusion_criteria=payload.inclusion_criteria,
            exclusion_criteria=payload.exclusion_criteria,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"PICO Query agent failed: {exc}"
        ) from exc
