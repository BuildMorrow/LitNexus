from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.conflict import ConflictEdge, EdgeRelationType, PaperClaim, ResearchGap
from app.models.paper import Paper, ScreeningStatus
from app.models.project import ResearchProject
from app.schemas.analysis import ConflictAnalysisOut, ConflictEdgeOut, ResearchGapOut
from app.services.conflict_engine import (
    ExtractedClaimSchema,
    cross_examine_claims,
    extract_paper_claims,
    synthesize_research_gaps,
)

router = APIRouter(prefix="/projects/{project_id}/conflicts", tags=["conflicts"])


@router.get("", response_model=ConflictAnalysisOut)
async def get_conflict_analysis(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    edges_res = await db.execute(
        select(ConflictEdge).where(ConflictEdge.project_id == project.id)
    )
    gaps_res = await db.execute(
        select(ResearchGap).where(ResearchGap.project_id == project.id)
    )
    return ConflictAnalysisOut(
        claims_extracted=0,
        edges_discovered=list(edges_res.scalars().all()),
        research_gaps=list(gaps_res.scalars().all()),
    )


@router.post("/analyze", response_model=ConflictAnalysisOut)
async def run_conflict_discovery(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    papers_res = await db.execute(
        select(Paper).where(
            Paper.project_id == project.id,
            Paper.screening_status == ScreeningStatus.included,
        )
    )
    included_papers = list(papers_res.scalars().all())
    if len(included_papers) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 included papers to run cross-paper conflict discovery.",
        )

    # Cap pairwise analysis for first iteration to control cost
    target_papers = included_papers[:10]
    extracted_pairs: list[tuple[Paper, PaperClaim, ExtractedClaimSchema]] = []

    for paper in target_papers:
        content = paper.abstract or paper.title
        claims_out = await extract_paper_claims(title=paper.title, content=content)
        for c in claims_out.claims[:1]:
            db_claim = PaperClaim(
                paper_id=paper.id,
                claim_text=c.claim_text,
                methodology=c.methodology,
                dataset=c.dataset,
                metric_summary=c.metric_summary,
                assumptions=c.assumptions,
                evidence_quote=c.evidence_quote,
            )
            db.add(db_claim)
            await db.flush()
            extracted_pairs.append((paper, db_claim, c))

    edges: list[ConflictEdge] = []
    conflict_summaries: list[str] = []

    for i in range(len(extracted_pairs)):
        for j in range(i + 1, len(extracted_pairs)):
            p_a, db_c_a, schema_a = extracted_pairs[i]
            p_b, db_c_b, schema_b = extracted_pairs[j]

            exam = await cross_examine_claims(p_a.title, schema_a, p_b.title, schema_b)
            rel_type = EdgeRelationType(exam.relation_type)

            edge = ConflictEdge(
                project_id=project.id,
                source_claim_id=db_c_a.id,
                target_claim_id=db_c_b.id,
                relation_type=rel_type,
                confidence=exam.confidence,
                debate_summary=exam.debate_summary,
                root_cause_hypothesis=exam.root_cause_hypothesis,
            )
            db.add(edge)
            edges.append(edge)

            if rel_type in (
                EdgeRelationType.contradicts,
                EdgeRelationType.assumption_mismatch,
            ):
                conflict_summaries.append(
                    f"[{rel_type.value}] {p_a.title} vs {p_b.title}: {exam.debate_summary} (Root cause: {exam.root_cause_hypothesis})"
                )

    gaps: list[ResearchGap] = []
    if conflict_summaries:
        gap_out = await synthesize_research_gaps(
            research_question=project.research_question,
            conflict_summaries=conflict_summaries,
        )
        for g in gap_out.gaps:
            db_gap = ResearchGap(
                project_id=project.id,
                title=g.title,
                description=g.description,
                suggested_direction=g.suggested_direction,
                novelty_score=g.novelty_score,
            )
            db.add(db_gap)
            gaps.append(db_gap)

    await db.commit()
    for e in edges:
        await db.refresh(e)
    for g in gaps:
        await db.refresh(g)

    return ConflictAnalysisOut(
        claims_extracted=len(extracted_pairs),
        edges_discovered=[ConflictEdgeOut.model_validate(e) for e in edges],
        research_gaps=[ResearchGapOut.model_validate(g) for g in gaps],
    )
