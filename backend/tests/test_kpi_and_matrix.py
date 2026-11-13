"""Test suite for Comparative Matrix and SLR KPI metrics endpoints."""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.api.v1.conflicts import get_comparative_matrix, get_kpi_metrics
from app.models.conflict import PaperClaim
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject


@pytest.mark.asyncio
async def test_get_comparative_matrix_returns_grounded_claims():
    proj_id = uuid.uuid4()
    mock_project = ResearchProject(id=proj_id, title="Test Project")

    paper_id = uuid.uuid4()
    mock_paper = Paper(
        id=paper_id,
        project_id=proj_id,
        title="Deep CNN for ECG",
        year=2024,
        scopus_quartile="Q1",
        screening_status=ScreeningStatus.included,
    )
    mock_claim = PaperClaim(
        id=uuid.uuid4(),
        paper_id=paper_id,
        claim_text="1D CNN achieves 98% accuracy on single-lead ECG.",
        methodology="1D-CNN",
        dataset="MIT-BIH",
        metric_summary="Accuracy=98%",
        assumptions=["Clean baseline"],
        evidence_quote="Our model reaches 98% accuracy on MIT-BIH.",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [(mock_claim, mock_paper)]
    mock_db.execute = AsyncMock(return_value=mock_result)

    res = await get_comparative_matrix(project=mock_project, db=mock_db)
    assert res.total_papers == 1
    assert res.total_claims == 1
    item = res.items[0]
    assert item.paper_title == "Deep CNN for ECG"
    assert item.scopus_quartile == "Q1"
    assert item.evidence_quote == "Our model reaches 98% accuracy on MIT-BIH."


@pytest.mark.asyncio
async def test_get_kpi_metrics_computes_hours_and_token_savings():
    proj_id = uuid.uuid4()
    mock_project = ResearchProject(id=proj_id, title="KPI Project")

    # 10 papers: 6 AL included/excluded, 2 LLM screened, 2 human labeled
    mock_papers = [
        Paper(
            id=uuid.uuid4(),
            project_id=proj_id,
            title=f"Paper {i}",
            screening_status=ScreeningStatus.included if i % 2 == 0 else ScreeningStatus.excluded,
            screening_source=(
                ScreeningSource.active_learning
                if i < 6
                else ScreeningSource.llm
                if i < 8
                else ScreeningSource.human
            ),
        )
        for i in range(10)
    ]

    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_papers
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute = AsyncMock(return_value=mock_result)

    res = await get_kpi_metrics(project=mock_project, db=mock_db)
    assert res.total_papers == 10
    assert res.active_learning_labeled == 6
    assert res.llm_labeled == 2
    assert res.human_labeled == 2
    # Automation rate: (6 AL + 2 LLM) / 10 = 80.0%
    assert res.automation_rate == 80.0
    # Token savings from AL: 6/10 = 60.0%
    assert res.token_savings_percentage == 60.0
    # Hours saved: 8 * 0.25h = 2.0h
    assert res.estimated_hours_saved == 2.0
