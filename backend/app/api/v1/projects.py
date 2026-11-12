from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned_project
from app.core.database import get_db
from app.models.project import ResearchProject
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut

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
