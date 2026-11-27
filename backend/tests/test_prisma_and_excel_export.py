"""Tests for Sprint E: PRISMA 2020 SVG generation, Excel (.xlsx) export, and Verbatim Gate."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock

from openpyxl import load_workbook

from app.api.v1.conflicts import export_first_draft_report, export_project_excel
from app.models.conflict import ConflictEdge, EdgeRelationType, PaperClaim, ResearchGap
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.models.project import ResearchProject
from app.services.prisma_export import generate_prisma_flow_svg, generate_slr_excel_bytes


def test_generate_prisma_flow_svg_contains_counts():
    svg = generate_prisma_flow_svg(identified=40, screened=40, excluded=28, included=12)
    assert "<svg" in svg
    assert "Records Identified (n = 40)" in svg
    assert "Excluded Studies (n = 28)" in svg
    assert "Final Included Corpus (n = 12)" in svg


def test_generate_slr_excel_bytes_readable_with_unicode():
    proj_id = uuid.uuid4()
    p1 = Paper(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="Mạng 1D CNN cho tín hiệu ECG đeo tay",
        authors=["Nguyễn, Nam"],
        journal="IEEE TBME",
        year=2025,
        scopus_quartile="Q1",
        screening_status=ScreeningStatus.included,
        screening_source=ScreeningSource.human,
        screening_rationale={"reason": "Phù hợp tiêu chí 1D CNN"},
    )
    c1 = PaperClaim(
        id=uuid.uuid4(),
        paper_id=p1.id,
        claim_text="Đạt 98.2% F1-score",
        methodology="1D-CNN",
        dataset="MIT-BIH",
        metric_summary="F1=0.982",
        assumptions=["Clean baseline"],
        evidence_quote="Achieves 98.2% F1 on MIT-BIH.",
        page_number=3,
        section_title="Results",
    )
    e1 = ConflictEdge(
        id=uuid.uuid4(),
        project_id=proj_id,
        source_claim_id=c1.id,
        target_claim_id=c1.id,
        relation_type=EdgeRelationType.contradicts,
        confidence=0.9,
        debate_summary="Clean vs noisy baseline difference.",
        root_cause_hypothesis="Motion artifact assumptions.",
    )
    g1 = ResearchGap(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="Adaptive Quantization",
        description="Dynamic noise resilience gap.",
        suggested_direction="Benchmark under ambulatory noise.",
        novelty_score=0.91,
    )

    xlsx_bytes = generate_slr_excel_bytes(
        project_title="ECG SLR",
        papers=[p1],
        claims_rows=[(c1, p1)],
        edges=[e1],
        gaps=[g1],
    )
    wb = load_workbook(io.BytesIO(xlsx_bytes))
    assert wb.sheetnames == ["Papers & Screening", "Evidence Matrix", "Conflicts & Gaps"]
    assert wb["Papers & Screening"]["A2"].value == "Mạng 1D CNN cho tín hiệu ECG đeo tay"
    assert wb["Evidence Matrix"]["I2"].value == "p.3 (Results)"


async def test_export_endpoints_return_svg_and_xlsx():
    proj_id = uuid.uuid4()
    proj = ResearchProject(
        id=proj_id, owner_id=uuid.uuid4(), title="Wearable SLR", research_question="Q"
    )
    p1 = Paper(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="Paper A",
        authors=["John Doe"],
        year=2025,
        screening_status=ScreeningStatus.included,
        screening_source=ScreeningSource.human,
    )

    papers_m = MagicMock()
    papers_m.scalars.return_value.all.return_value = [p1]
    claims_m = MagicMock()
    claims_m.all.return_value = []
    edges_m = MagicMock()
    edges_m.scalars.return_value.all.return_value = []
    gaps_m = MagicMock()
    gaps_m.scalars.return_value.all.return_value = []

    db_draft = AsyncMock()
    db_draft.execute = AsyncMock(side_effect=[papers_m, claims_m, edges_m, gaps_m])
    draft = await export_first_draft_report(project=proj, db=db_draft)
    assert "<svg" in draft.prisma_svg

    db_xlsx = AsyncMock()
    db_xlsx.execute = AsyncMock(side_effect=[papers_m, claims_m, edges_m, gaps_m])
    resp = await export_project_excel(project=proj, db=db_xlsx)
    assert resp.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
