from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.paper import Paper
from app.models.project import ResearchProject
from app.schemas.paper import PaperOut, SearchRequest
from app.services.academic_search import search_openalex

router = APIRouter(prefix="/projects/{project_id}", tags=["search"])


@router.get("/papers", response_model=list[PaperOut])
async def list_project_papers(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Paper)
        .where(Paper.project_id == project.id)
        .order_by(Paper.al_uncertainty_score.desc().nulls_last(), Paper.citation_count.desc())
    )
    return list(result.scalars().all())


@router.post("/search", response_model=list[PaperOut])
async def search_and_ingest_papers(
    payload: SearchRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    works = await search_openalex(
        query=payload.query,
        limit=payload.limit,
        year_from=payload.year_from,
        year_to=payload.year_to,
        open_access_only=payload.open_access_only,
    )

    existing_res = await db.execute(
        select(Paper.doi, Paper.openalex_id).where(Paper.project_id == project.id)
    )
    existing_rows = existing_res.all()
    known_dois = {r[0] for r in existing_rows if r[0]}
    known_oa = {r[1] for r in existing_rows if r[1]}

    added: list[Paper] = []
    for work in works:
        if (work.doi and work.doi in known_dois) or (
            work.openalex_id and work.openalex_id in known_oa
        ):
            continue

        paper = Paper(
            project_id=project.id,
            openalex_id=work.openalex_id,
            doi=work.doi,
            title=work.title,
            authors=work.authors,
            journal=work.journal,
            issn=work.issn,
            year=work.year,
            abstract=work.abstract,
            citation_count=work.citation_count,
            pdf_url=work.pdf_url,
            scopus_quartile=work.scopus_quartile,
        )
        db.add(paper)
        added.append(paper)
        if work.doi:
            known_dois.add(work.doi)
        if work.openalex_id:
            known_oa.add(work.openalex_id)

    await db.commit()
    for p in added:
        await db.refresh(p)
    return added
