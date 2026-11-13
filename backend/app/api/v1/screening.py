import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject
from app.schemas.paper import (
    ActiveLearningSummary,
    LLMBatchScreenRequest,
    LLMBatchScreenResponse,
    LLMScreeningDecision,
    PaperLabelRequest,
    PaperOut,
)
from app.services.active_screener import ActiveLearningScreener, LabeledSample
from app.services.llm_router import llm_router
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects/{project_id}/screening", tags=["screening"])


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
        paper.screening_rationale = {"human_note": payload.reason}

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

        if p.screening_source in (ScreeningSource.human, ScreeningSource.llm) and p.screening_status in (
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
    Enforces Human-in-the-Loop review by attaching verifiable rationales and quotes.
    """
    # Fetch papers that are uncertain or unscreened, prioritizing highest uncertainty
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

    # Format criteria & papers into prompt
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
2. If included, assign status "included". If excluded, assign status "excluded".
3. Provide a clear, scholarly rationale in "reason".
4. CRITICAL GROUNDING RULE: You MUST provide a verbatim sentence from the title or abstract in "evidence_quote" as proof. Never hallucinate evidence quotes.
5. Provide a confidence score between 0.0 and 1.0.
"""

    system_prompt = (
        "You are an evidence-grounded academic screener. You strictly assess scientific abstracts "
        "and provide exact quotes to prevent hallucination."
    )

    llm_output = await llm_router.generate_structured(
        prompt=prompt,
        schema=_LLMDecisionsPayload,
        system_prompt=system_prompt,
        temperature=0.1,
    )

    paper_map = {str(p.id): p for p in candidate_papers}
    applied_decisions: list[LLMScreeningDecision] = []
    auto_inc = 0
    auto_exc = 0

    for dec in llm_output.decisions:
        if dec.paper_id in paper_map:
            paper = paper_map[dec.paper_id]
            paper.screening_status = dec.status
            paper.screening_source = ScreeningSource.llm
            paper.screening_rationale = {
                "reason": dec.reason,
                "evidence_quote": dec.evidence_quote,
                "confidence": dec.confidence,
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
