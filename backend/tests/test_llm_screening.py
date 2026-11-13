"""Test suite for LLM batch screening and evidence quote grounding."""

from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from pydantic import BaseModel
import pytest

from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject
from app.schemas.paper import LLMBatchScreenRequest, LLMScreeningDecision


@pytest.mark.asyncio
async def test_auto_label_uncertain_with_evidence_quote():
    from app.api.v1.screening import _LLMDecisionsPayload, auto_label_uncertain_papers

    mock_project = ResearchProject(
        id=uuid.uuid4(),
        title="Arrhythmia Detection SLR",
        research_question="How effective are 1D CNNs for wearable ECG arrhythmia detection?",
        inclusion_criteria=["Uses 1D CNN", "Wearable or single-lead ECG"],
        exclusion_criteria=["Animal studies", "Review articles without benchmark"],
    )

    paper_id = uuid.uuid4()
    mock_paper = Paper(
        id=paper_id,
        project_id=mock_project.id,
        title="1D Convolutional Neural Network for Wearable ECG",
        abstract="We achieve 98% accuracy on single-lead ECG with a 1D CNN architecture.",
        screening_status=ScreeningStatus.uncertain,
        screening_source=ScreeningSource.none,
    )

    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_paper]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_llm_decision = LLMScreeningDecision(
        paper_id=str(paper_id),
        status=ScreeningStatus.included,
        confidence=0.95,
        reason="Directly uses 1D CNN on wearable ECG.",
        evidence_quote="We achieve 98% accuracy on single-lead ECG with a 1D CNN architecture.",
    )

    with patch(
        "app.api.v1.screening.llm_router.generate_structured",
        new=AsyncMock(return_value=_LLMDecisionsPayload(decisions=[mock_llm_decision])),
    ):
        req = LLMBatchScreenRequest(limit=10)
        res = await auto_label_uncertain_papers(
            payload=req,
            project=mock_project,
            db=mock_db,
        )

        assert res.processed_count == 1
        assert res.auto_included == 1
        assert res.auto_excluded == 0
        assert mock_paper.screening_status == ScreeningStatus.included
        assert mock_paper.screening_source == ScreeningSource.llm
        assert mock_paper.screening_rationale["evidence_quote"] == mock_llm_decision.evidence_quote
        assert mock_db.commit.called
