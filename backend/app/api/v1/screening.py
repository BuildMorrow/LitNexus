import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject
from app.schemas.paper import ActiveLearningSummary, PaperLabelRequest, PaperOut
from app.services.active_screener import ActiveLearningScreener, LabeledSample

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
