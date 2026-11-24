"""Test suite for Conflict Graph topology and First Draft Export endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.api.v1.conflicts import export_first_draft_report, get_conflict_graph
from app.models.conflict import ConflictEdge, EdgeRelationType, PaperClaim, ResearchGap
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject


@pytest.mark.asyncio
async def test_get_conflict_graph_formats_nodes_and_edges():
    proj_id = uuid.uuid4()
    mock_project = ResearchProject(id=proj_id, title="Arrhythmia Project")

    paper_id = uuid.uuid4()
    mock_paper = Paper(
        id=paper_id,
        project_id=proj_id,
        title="Lightweight 1D CNN",
        year=2024,
        scopus_quartile="Q1",
        screening_status=ScreeningStatus.included,
    )

    claim_1 = PaperClaim(
        id=uuid.uuid4(),
        paper_id=paper_id,
        claim_text="1D CNN achieves high F1 with low power.",
        methodology="1D-CNN",
        dataset="MIT-BIH",
        metric_summary="F1=0.98",
        assumptions=["Clean baseline"],
        evidence_quote="Reaches 98% on MIT-BIH.",
    )
    claim_2 = PaperClaim(
        id=uuid.uuid4(),
        paper_id=paper_id,
        claim_text="Quantization degrades accuracy by 4% under noise.",
        methodology="Quantized 1D-CNN",
        dataset="Wearable",
        metric_summary="Accuracy=94%",
        assumptions=["Motion artifacts"],
        evidence_quote="Accuracy drops to 94%.",
    )

    edge_1 = ConflictEdge(
        id=uuid.uuid4(),
        project_id=proj_id,
        source_claim_id=claim_1.id,
        target_claim_id=claim_2.id,
        relation_type=EdgeRelationType.contradicts,
        confidence=0.90,
        debate_summary="Paper A shows high robustness while Paper B observes accuracy degradation under noise.",
        root_cause_hypothesis="Different baseline noise assumptions.",
    )

    gap_1 = ResearchGap(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="Robust Quantization Under High Motion Artifacts",
        description="Investigating noise-adaptive quantization schemes.",
        suggested_direction="Evaluate adaptive bit-depth scaling on ambulatory data.",
        novelty_score=0.88,
    )

    mock_db = AsyncMock()

    # Sequence of queries: edges, gaps, claims
    edges_mock = MagicMock()
    edges_mock.scalars.return_value.all.return_value = [edge_1]

    gaps_mock = MagicMock()
    gaps_mock.scalars.return_value.all.return_value = [gap_1]

    claims_mock = MagicMock()
    claims_mock.all.return_value = [(claim_1, mock_paper), (claim_2, mock_paper)]

    mock_db.execute = AsyncMock(side_effect=[edges_mock, gaps_mock, claims_mock])

    res = await get_conflict_graph(project=mock_project, db=mock_db)

    assert res.total_nodes == 2
    assert res.total_edges == 1
    assert res.contradiction_count == 1
    assert res.nodes[0].quartile == "Q1"
    assert res.edges[0].relation_type == EdgeRelationType.contradicts
    assert len(res.research_gaps) == 1


@pytest.mark.asyncio
async def test_export_first_draft_report_generates_markdown_and_bibtex():
    proj_id = uuid.uuid4()
    mock_project = ResearchProject(
        id=proj_id,
        title="Wearable ECG SLR",
        research_question="How effective are lightweight 1D CNNs on wearable ECG devices?",
    )

    p1 = Paper(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="Compact 1D CNN for Wearable ECG",
        authors=["Wei Zhang", "John Smith"],
        year=2024,
        journal="IEEE Transactions on Biomedical Engineering",
        doi="10.1109/TBME.2024.123456",
        screening_status=ScreeningStatus.included,
    )
    p2 = Paper(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="Heavy 2D CNN Spectrogram Review",
        authors=["Alice Doe"],
        year=2023,
        screening_status=ScreeningStatus.excluded,
    )

    c1 = PaperClaim(
        id=uuid.uuid4(),
        paper_id=p1.id,
        claim_text="1D CNN achieves 98.2% F1 on wearable ECG.",
        methodology="1D-CNN",
        dataset="MIT-BIH",
        metric_summary="F1=0.982",
        evidence_quote="Our model achieves 98.2% F1 on single-lead patches.",
    )

    mock_db = AsyncMock()

    papers_mock = MagicMock()
    papers_mock.scalars.return_value.all.return_value = [p1, p2]

    claims_mock = MagicMock()
    claims_mock.all.return_value = [(c1, p1)]

    edges_mock = MagicMock()
    edges_mock.scalars.return_value.all.return_value = []

    gaps_mock = MagicMock()
    gaps_mock.scalars.return_value.all.return_value = []

    mock_db.execute = AsyncMock(side_effect=[papers_mock, claims_mock, edges_mock, gaps_mock])

    draft_res = await export_first_draft_report(project=mock_project, db=mock_db)

    assert draft_res.total_references == 1
    assert "@article" in draft_res.bibtex_content
    assert "Zhang2024" in draft_res.bibtex_content
    assert "# Systematic Literature Review: Wearable ECG SLR" in draft_res.draft_markdown
    assert "PRISMA 2020" in draft_res.draft_markdown
    assert "Our model achieves 98.2% F1 on single-lead patches." in draft_res.draft_markdown
    assert draft_res.prisma_flow_summary["included"] == 1
    assert draft_res.prisma_flow_summary["excluded"] == 1
