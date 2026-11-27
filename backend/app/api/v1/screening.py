import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.chunk import PaperChunk
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject
from app.schemas.paper import (
    ActiveLearningSummary,
    DualPeerScreenResponse,
    HITLOverrideRequest,
    LLMBatchScreenRequest,
    LLMBatchScreenResponse,
    LLMScreeningDecision,
    PaperLabelRequest,
    PaperOut,
    QualityGateStatus,
)
from app.services.active_screener import ActiveLearningScreener, LabeledSample
from app.services.grounding_verifier import verify_quotes
from app.services.llm_router import llm_router
from app.services.peer_screener import dual_peer_screen_paper

router = APIRouter(prefix="/projects/{project_id}/screening", tags=["screening"])

GROUNDING_GATE_THRESHOLD = 0.80
MIN_INCLUDED_PAPERS = 3


def compute_project_quality_gate(
    papers: list[Paper],
    *,
    grounding_threshold: float = GROUNDING_GATE_THRESHOLD,
    min_papers: int = MIN_INCLUDED_PAPERS,
) -> QualityGateStatus:
    """Compute deterministic Grounding Gate >= 80% and corpus sufficiency check."""
    included = [p for p in papers if p.screening_status == ScreeningStatus.included]
    grounding_scores: list[float] = []
    for p in included:
        rationale = p.screening_rationale or {}
        if rationale.get("hitl_approved"):
            grounding_scores.append(1.0)
            continue
        if "grounding_score" in rationale:
            grounding_scores.append(float(rationale["grounding_score"]))
        elif rationale.get("evidence_quote"):
            segments = [(f"{p.title}. {p.abstract or ''}", None)]
            _, score = verify_quotes([str(rationale["evidence_quote"])], segments)
            grounding_scores.append(score)

    precision = round(sum(grounding_scores) / len(grounding_scores), 4) if grounding_scores else 1.0
    warnings: list[str] = []
    if len(included) < min_papers:
        warnings.append(
            f"Corpus nhỏ ({len(included)}/{min_papers} bài Included). Cần mở rộng tìm kiếm hoặc Snowballing."
        )
    if grounding_scores and precision < grounding_threshold:
        warnings.append(
            f"Grounding Precision ({precision:.0%}) thấp hơn ngưỡng chuẩn ({grounding_threshold:.0%}). "
            "Cần rà soát HITL trước khi xuất bản thảo chính thức."
        )

    passed = len(included) >= min_papers and (not grounding_scores or precision >= grounding_threshold)
    return QualityGateStatus(
        passed=passed,
        grounding_precision=precision,
        grounding_threshold=grounding_threshold,
        included_count=len(included),
        min_papers=min_papers,
        requires_hitl_review=not passed,
        warnings=warnings,
    )


@router.get("/quality-gate", response_model=QualityGateStatus)
async def get_quality_gate_status(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Paper).where(Paper.project_id == project.id))
    return compute_project_quality_gate(list(result.scalars().all()))


@router.patch("/papers/{paper_id}/label", response_model=PaperOut)
async def label_paper(
    paper_id: uuid.UUID,
    payload: PaperLabelRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.project_id == project.id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in project")

    paper.screening_status = payload.status
    paper.screening_source = ScreeningSource.human
    if payload.reason:
        paper.screening_rationale = {"human_note": payload.reason, "hitl_approved": True}
    else:
        paper.screening_rationale = {**(paper.screening_rationale or {}), "hitl_approved": True}

    await db.commit()
    await db.refresh(paper)
    return paper


@router.post("/papers/{paper_id}/hitl-override", response_model=PaperOut)
async def hitl_override_paper(
    paper_id: uuid.UUID,
    payload: HITLOverrideRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Explicit Human-in-the-Loop approval or override of an AI screening verdict."""
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.project_id == project.id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in project")

    action = payload.action.strip().lower()
    if action == "include":
        paper.screening_status = ScreeningStatus.included
    elif action == "exclude":
        paper.screening_status = ScreeningStatus.excluded
    elif action != "approve":
        raise HTTPException(status_code=400, detail="Action must be 'approve', 'include', or 'exclude'")

    paper.screening_source = ScreeningSource.human
    paper.screening_rationale = {
        **(paper.screening_rationale or {}),
        "hitl_approved": True,
        "hitl_action": action,
        "human_note": payload.note or "Verified by researcher HITL review",
    }
    await db.commit()
    await db.refresh(paper)
    return paper


@router.post("/run-active-learning", response_model=ActiveLearningSummary)
async def run_active_learning(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Paper).where(Paper.project_id == project.id))
    papers = list(result.scalars().all())

    labeled: list[LabeledSample] = []
    unlabeled: list[tuple[str, str]] = []
    paper_map: dict[str, Paper] = {}

    for p in papers:
        pid = str(p.id)
        paper_map[pid] = p
        text = f"{p.title}. {p.abstract or ''}".strip()

        if p.screening_source in (
            ScreeningSource.human,
            ScreeningSource.llm,
        ) and p.screening_status in (
            ScreeningStatus.included,
            ScreeningStatus.excluded,
        ):
            labeled.append(
                LabeledSample(
                    paper_id=pid,
                    text=text,
                    label=1 if p.screening_status == ScreeningStatus.included else 0,
                )
            )
        else:
            unlabeled.append((pid, text))

    screener = ActiveLearningScreener()
    predictions = screener.train_and_score(labeled=labeled, unlabeled=unlabeled)

    auto_inc = 0
    auto_exc = 0
    needs_rev = 0

    for pred in predictions:
        paper = paper_map[pred.paper_id]
        paper.al_inclusion_prob = pred.inclusion_prob
        paper.al_uncertainty_score = pred.uncertainty_score

        if pred.suggested_action == "auto_include":
            paper.screening_status = ScreeningStatus.included
            paper.screening_source = ScreeningSource.active_learning
            auto_inc += 1
        elif pred.suggested_action == "auto_exclude":
            paper.screening_status = ScreeningStatus.excluded
            paper.screening_source = ScreeningSource.active_learning
            auto_exc += 1
        else:
            paper.screening_status = ScreeningStatus.uncertain
            needs_rev += 1

    await db.commit()

    return ActiveLearningSummary(
        total_papers=len(papers),
        labeled_count=len(labeled),
        auto_included=auto_inc,
        auto_excluded=auto_exc,
        needs_review=needs_rev,
    )


class _LLMDecisionsPayload(BaseModel):
    decisions: list[LLMScreeningDecision] = Field(default_factory=list)


@router.post("/auto-label-uncertain", response_model=LLMBatchScreenResponse)
async def auto_label_uncertain_papers(
    payload: LLMBatchScreenRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Use centralized LLM to screen top uncertain papers with strict evidence grounding (quotes).
    Verifies quotes deterministically before saving.
    """
    query = (
        select(Paper)
        .where(
            Paper.project_id == project.id,
            Paper.screening_status.in_([ScreeningStatus.uncertain, ScreeningStatus.unscreened]),
        )
        .order_by(Paper.al_uncertainty_score.desc().nulls_last(), Paper.citation_count.desc())
        .limit(payload.limit)
    )
    result = await db.execute(query)
    candidate_papers = list(result.scalars().all())

    if not candidate_papers:
        return LLMBatchScreenResponse(
            processed_count=0,
            auto_included=0,
            auto_excluded=0,
            decisions=[],
        )

    pico_str = str(project.pico_framework or {})
    inc_str = ", ".join(project.inclusion_criteria) if project.inclusion_criteria else "None"
    exc_str = ", ".join(project.exclusion_criteria) if project.exclusion_criteria else "None"

    papers_text_block = "\n\n".join(
        f"--- Paper ID: {str(p.id)} ---\n"
        f"Title: {p.title}\n"
        f"Abstract: {p.abstract or 'No abstract available'}\n"
        for p in candidate_papers
    )

    prompt = f"""
You are an expert academic screener conducting a Systematic Literature Review.
Review the candidate papers against the Project research scope and criteria.

[Research Question]: {project.research_question or project.title}
[PICO Framework]: {pico_str}
[Inclusion Criteria]: {inc_str}
[Exclusion Criteria]: {exc_str}

Candidates to screen:
{papers_text_block}

INSTRUCTIONS:
1. For every candidate paper, decide whether it should be "included" or "excluded".
2. Provide a clear, scholarly rationale in "reason".
3. CRITICAL GROUNDING RULE: Provide a verbatim sentence from the title or abstract in "evidence_quote". Never hallucinate quotes.
4. Provide a confidence score between 0.0 and 1.0.
"""

    llm_output = await llm_router.generate_structured(
        prompt=prompt,
        schema=_LLMDecisionsPayload,
        system_prompt="You are an evidence-grounded academic screener. Provide exact verbatim quotes.",
        temperature=0.1,
    )

    paper_map = {str(p.id): p for p in candidate_papers}
    applied_decisions: list[LLMScreeningDecision] = []
    auto_inc = 0
    auto_exc = 0

    for dec in llm_output.decisions:
        if dec.paper_id in paper_map:
            paper = paper_map[dec.paper_id]
            segments = [(f"{paper.title}. {paper.abstract or ''}", None)]
            _, grounding_score = verify_quotes([dec.evidence_quote], segments)

            paper.screening_status = dec.status
            paper.screening_source = ScreeningSource.llm
            paper.screening_rationale = {
                "reason": dec.reason,
                "evidence_quote": dec.evidence_quote,
                "confidence": dec.confidence,
                "grounding_score": grounding_score,
                "model_assisted": True,
            }
            if dec.status == ScreeningStatus.included:
                auto_inc += 1
            elif dec.status == ScreeningStatus.excluded:
                auto_exc += 1
            applied_decisions.append(dec)

    await db.commit()

    return LLMBatchScreenResponse(
        processed_count=len(applied_decisions),
        auto_included=auto_inc,
        auto_excluded=auto_exc,
        decisions=applied_decisions,
    )


@router.post("/dual-peer-screen", response_model=DualPeerScreenResponse)
async def dual_peer_screen_uncertain(
    payload: LLMBatchScreenRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Run blind Dual-Agent Peer Screening (Inclusive vs Strict + Adjudicator on disagreement)
    exclusively on uncertain/unscreened papers, verified by deterministic grounding.
    """
    query = (
        select(Paper)
        .where(
            Paper.project_id == project.id,
            Paper.screening_status.in_([ScreeningStatus.uncertain, ScreeningStatus.unscreened]),
        )
        .order_by(Paper.al_uncertainty_score.desc().nulls_last(), Paper.citation_count.desc())
        .limit(payload.limit)
    )
    res = await db.execute(query)
    candidates = list(res.scalars().all())

    if not candidates:
        all_res = await db.execute(select(Paper).where(Paper.project_id == project.id))
        gate = compute_project_quality_gate(list(all_res.scalars().all()))
        return DualPeerScreenResponse(
            processed_count=0,
            included_count=0,
            excluded_count=0,
            uncertain_count=0,
            disagreement_count=0,
            avg_grounding_score=1.0,
            quality_gate=gate,
        )

    # Gather full-text chunks if PDF was already ingested for stronger grounding
    chunk_res = await db.execute(
        select(PaperChunk).where(PaperChunk.paper_id.in_([p.id for p in candidates]))
    )
    chunks_by_paper: dict[uuid.UUID, list[tuple[str, int | None]]] = {}
    for ch in chunk_res.scalars().all():
        chunks_by_paper.setdefault(ch.paper_id, []).append((ch.content, ch.page_number))

    semaphore = asyncio.Semaphore(4)

    async def _run_one(p: Paper):
        async with semaphore:
            segments = chunks_by_paper.get(p.id) or [(f"{p.title}. {p.abstract or ''}", None)]
            excerpt = "\n".join(seg[0] for seg in segments[:4])[:4500]
            return p, await dual_peer_screen_paper(
                paper_id=str(p.id),
                title=p.title,
                abstract=excerpt,
                segments=segments,
                research_question=project.research_question or project.title,
                inclusion_criteria=project.inclusion_criteria or [],
                exclusion_criteria=project.exclusion_criteria or [],
            )

    outcomes = await asyncio.gather(*(_run_one(p) for p in candidates))

    inc_cnt = 0
    exc_cnt = 0
    unc_cnt = 0
    disagree_cnt = 0
    grounding_scores: list[float] = []

    for paper, verdict in outcomes:
        paper.screening_status = ScreeningStatus(verdict.final_decision)
        paper.screening_source = ScreeningSource.llm
        paper.screening_rationale = {
            "mode": "dual_peer_review",
            "reason": verdict.final_reason,
            "confidence": verdict.confidence,
            "disagreed": verdict.disagreed,
            "grounding_score": verdict.grounding_score,
            "verified_quotes": verdict.verified_quotes,
            "evidence_quote": verdict.verified_quotes[0] if verdict.verified_quotes else "",
            "opinions": [op.model_dump() for op in verdict.opinions],
        }
        grounding_scores.append(verdict.grounding_score)
        if verdict.disagreed:
            disagree_cnt += 1
        if verdict.final_decision == "included":
            inc_cnt += 1
        elif verdict.final_decision == "excluded":
            exc_cnt += 1
        else:
            unc_cnt += 1

    await db.commit()

    all_papers_res = await db.execute(select(Paper).where(Paper.project_id == project.id))
    gate = compute_project_quality_gate(list(all_papers_res.scalars().all()))
    avg_g = round(sum(grounding_scores) / len(grounding_scores), 4) if grounding_scores else 1.0

    return DualPeerScreenResponse(
        processed_count=len(outcomes),
        included_count=inc_cnt,
        excluded_count=exc_cnt,
        uncertain_count=unc_cnt,
        disagreement_count=disagree_cnt,
        avg_grounding_score=avg_g,
        quality_gate=gate,
    )
