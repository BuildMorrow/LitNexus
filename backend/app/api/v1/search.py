import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.chunk import PaperChunk
from app.models.paper import Paper
from app.models.project import ResearchProject
from app.schemas.paper import PaperOut, SearchRequest
from app.services.academic_search import search_openalex
from app.services.pdf_processor import pdf_processor

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

    # Clear existing chunks if any
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
