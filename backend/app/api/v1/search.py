import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.chunk import PaperChunk
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject
from app.models.search_query import SearchQuery
from app.schemas.paper import (
    PaperOut,
    SearchQueryOut,
    SearchRequest,
    SnowballRequest,
    SnowballResponse,
)
from app.services.academic_search import (
    ScholarlyWork,
    run_two_way_snowball,
    search_openalex,
)
from app.services.pdf_processor import pdf_processor
from app.services.sjr_service import sjr_service

router = APIRouter(prefix="/projects/{project_id}", tags=["search"])


async def _persist_works_dedup(
    db: AsyncSession,
    project: ResearchProject,
    works: list[ScholarlyWork],
    *,
    query_string: str,
    source_type: str,
) -> list[Paper]:
    """Deduplicate works against existing project papers, enrich quartile, and log search history."""
    existing_res = await db.execute(
        select(Paper.doi, Paper.openalex_id, Paper.title).where(Paper.project_id == project.id)
    )
    existing_rows = existing_res.all()
    known_dois = {r[0].lower() for r in existing_rows if r[0]}
    known_oa = {r[1] for r in existing_rows if r[1]}
    known_titles = {r[2].strip().lower() for r in existing_rows if r[2]}

    added: list[Paper] = []
    for work in works:
        doi_norm = work.doi.lower() if work.doi else None
        title_norm = work.title.strip().lower()
        if (
            (doi_norm and doi_norm in known_dois)
            or (work.openalex_id and work.openalex_id in known_oa)
            or (title_norm in known_titles)
        ):
            continue

        quartile = work.scopus_quartile
        if not quartile and (work.issn or work.journal):
            sjr_res = await sjr_service.lookup_db_first(
                db=db, issn=work.issn, journal_title=work.journal
            )
            quartile = sjr_res.quartile

        paper = Paper(
            id=uuid.uuid4(),
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
            scopus_quartile=quartile,
            discovery_source=work.discovery_source,
            seed_distance=work.seed_distance,
            screening_status=ScreeningStatus.unscreened,
            screening_source=ScreeningSource.none,
        )
        db.add(paper)
        added.append(paper)
        if doi_norm:
            known_dois.add(doi_norm)
        if work.openalex_id:
            known_oa.add(work.openalex_id)
        known_titles.add(title_norm)

    db.add(
        SearchQuery(
            project_id=project.id,
            query_string=query_string,
            source_type=source_type,
            result_count=len(added),
        )
    )
    await db.commit()
    for p in added:
        await db.refresh(p)
    return added


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


@router.get("/search/history", response_model=list[SearchQueryOut])
async def list_search_history(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Return project-scoped search and snowball history ordered by newest first."""
    result = await db.execute(
        select(SearchQuery)
        .where(SearchQuery.project_id == project.id)
        .order_by(SearchQuery.created_at.desc())
        .limit(30)
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
    return await _persist_works_dedup(
        db=db,
        project=project,
        works=works,
        query_string=payload.query,
        source_type="keyword",
    )


@router.post("/search/snowball", response_model=SnowballResponse)
async def snowball_papers(
    payload: SnowballRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Expand seed papers via bidirectional (backward & forward) OpenAlex citation snowballing."""
    seed_res = await db.execute(
        select(Paper).where(
            Paper.project_id == project.id,
            Paper.id.in_(payload.seed_paper_ids),
        )
    )
    seed_papers = list(seed_res.scalars().all())
    if not seed_papers:
        raise HTTPException(
            status_code=404, detail="No matching seed papers found in this project."
        )

    seed_oa_ids = [p.openalex_id for p in seed_papers if p.openalex_id]
    if not seed_oa_ids:
        raise HTTPException(
            status_code=400,
            detail="Selected seed papers lack OpenAlex IDs required for citation snowballing.",
        )

    works = await run_two_way_snowball(
        seed_openalex_ids=seed_oa_ids,
        limit_per_direction=payload.limit_per_direction,
        distance=payload.distance,
    )
    added = await _persist_works_dedup(
        db=db,
        project=project,
        works=works,
        query_string=f"Snowball ({len(seed_oa_ids)} seeds, depth={payload.distance})",
        source_type="two_way_snowball",
    )
    backward_count = sum(1 for p in added if p.discovery_source == "backward_snowball")
    forward_count = sum(1 for p in added if p.discovery_source == "forward_snowball")
    return SnowballResponse(
        seeds_used=len(seed_oa_ids),
        added_count=len(added),
        backward_count=backward_count,
        forward_count=forward_count,
        papers=added,
    )


@router.post("/papers/{paper_id}/ingest-pdf", status_code=status.HTTP_200_OK)
async def ingest_paper_pdf(
    paper_id: uuid.UUID,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Download and parse full-text PDF for an included paper.
    Chunks text with page pinning and section detection into paper_chunks table.
    """
    res = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.project_id == project.id)
    )
    paper = res.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in project")

    if not paper.pdf_url:
        raise HTTPException(
            status_code=400,
            detail="Paper does not have a verified Open Access pdf_url available for download.",
        )

    try:
        chunks = await pdf_processor.download_and_process_pdf(paper.pdf_url)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch or parse PDF from {paper.pdf_url}: {exc}",
        ) from exc

    existing_chunks = await db.execute(select(PaperChunk).where(PaperChunk.paper_id == paper.id))
    for ec in existing_chunks.scalars().all():
        await db.delete(ec)

    for ch in chunks:
        db_chunk = PaperChunk(
            paper_id=paper.id,
            chunk_index=ch.chunk_index,
            page_number=ch.page_number,
            section_title=ch.section_title,
            content=ch.content,
        )
        db.add(db_chunk)

    await db.commit()
    return {
        "status": "success",
        "paper_id": str(paper.id),
        "chunks_indexed": len(chunks),
        "pages_processed": max([c.page_number for c in chunks], default=0),
    }
