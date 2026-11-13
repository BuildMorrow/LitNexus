from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.conflict import ConflictEdge, EdgeRelationType, PaperClaim, ResearchGap
from app.models.paper import Paper, ScreeningStatus
from app.models.project import ResearchProject
from app.schemas.analysis import (
    ComparativeMatrixItem,
    ComparativeMatrixResponse,
    ConflictAnalysisOut,
    ConflictEdgeOut,
    KPIMetricsResponse,
    ResearchGapOut,
)
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


@router.get("/comparative-matrix", response_model=ComparativeMatrixResponse)
async def get_comparative_matrix(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Get structured comparative evidence matrix across all included papers.
    Grounds all comparisons strictly on extracted claims and verbatim evidence quotes.
    """
    query = (
        select(PaperClaim, Paper)
        .join(Paper, PaperClaim.paper_id == Paper.id)
        .where(
            Paper.project_id == project.id,
            Paper.screening_status == ScreeningStatus.included,
        )
        .order_by(Paper.year.desc().nulls_last(), Paper.citation_count.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    items = [
        ComparativeMatrixItem(
            paper_id=paper.id,
            paper_title=paper.title,
            year=paper.year,
            scopus_quartile=paper.scopus_quartile,
            claim_id=claim.id,
            claim_text=claim.claim_text,
            methodology=claim.methodology,
            dataset=claim.dataset,
            metric_summary=claim.metric_summary,
            assumptions=claim.assumptions or [],
            evidence_quote=claim.evidence_quote,
        )
        for claim, paper in rows
    ]

    distinct_paper_ids = {paper.id for _, paper in rows}
    return ComparativeMatrixResponse(
        total_papers=len(distinct_paper_ids),
        total_claims=len(items),
        items=items,
    )


@router.get("/kpi-metrics", response_model=KPIMetricsResponse)
async def get_kpi_metrics(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Compute core SLR efficiency and accuracy KPI metrics:
    - Token savings percentage
    - Estimated research hours saved (assuming 15m manual review per paper)
    - Automated vs Human-in-the-Loop decision ratio
    """
    result = await db.execute(select(Paper).where(Paper.project_id == project.id))
    papers = list(result.scalars().all())
    total = len(papers)

    if total == 0:
        return KPIMetricsResponse(
            total_papers=0,
            included_count=0,
            excluded_count=0,
            uncertain_count=0,
            unscreened_count=0,
            human_labeled=0,
            llm_labeled=0,
            active_learning_labeled=0,
            automation_rate=0.0,
            token_savings_percentage=0.0,
            estimated_hours_saved=0.0,
        )

    included = sum(1 for p in papers if p.screening_status == ScreeningStatus.included)
    excluded = sum(1 for p in papers if p.screening_status == ScreeningStatus.excluded)
    uncertain = sum(1 for p in papers if p.screening_status == ScreeningStatus.uncertain)
    unscreened = sum(1 for p in papers if p.screening_status == ScreeningStatus.unscreened)

    human = sum(1 for p in papers if p.screening_source.value == "human")
    llm = sum(1 for p in papers if p.screening_source.value == "llm")
    al = sum(1 for p in papers if p.screening_source.value == "active_learning")

    # Papers processed automatically without human reading
    auto_handled = al + llm
    automation_rate = round((auto_handled / total) * 100, 2)

    # Active learning classifies ~90% with 0 LLM tokens.
    # LLM calls are restricted only to borderline papers.
    # If all papers were read via LLM, token cost would be 100%.
    # With AL auto-handling, token saving is proportional to AL handled papers.
    token_savings = round((al / total) * 100, 2)

    # Hours saved: 15 minutes (0.25h) per auto-handled paper
    hours_saved = round(auto_handled * 0.25, 2)

    return KPIMetricsResponse(
        total_papers=total,
        included_count=included,
        excluded_count=excluded,
        uncertain_count=uncertain,
        unscreened_count=unscreened,
        human_labeled=human,
        llm_labeled=llm,
        active_learning_labeled=al,
        automation_rate=automation_rate,
        token_savings_percentage=token_savings,
        estimated_hours_saved=hours_saved,
    )
