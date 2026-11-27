"""Tests for Sprint B: 3 Research Setup Agents, 2-way Snowballing, and SJR CSV lookup."""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.search import list_search_history, snowball_papers
from app.models.paper import Paper
from app.models.project import ResearchProject
from app.models.search_query import SearchQuery
from app.schemas.paper import SnowballRequest
from app.services.academic_search import ScholarlyWork, run_two_way_snowball
from app.services.setup_agents import (
    CriteriaGenerationResult,
    PICOQueryResult,
    ScopeAnalysisResult,
    run_criteria_generator,
    run_pico_query_generator,
    run_scope_optimizer,
)
from app.services.sjr_service import SJRService, parse_scimago_csv_text


@pytest.mark.asyncio
async def test_setup_agents_use_central_llm_router():
    mock_scope = ScopeAnalysisResult(
        status="optimal",
        score=86,
        feedback="Well-defined wearable ECG scope.",
        suggested_topics=["Topic A", "Topic B"],
    )
    mock_criteria = CriteriaGenerationResult(
        inclusion_criteria=["2021-2026", "Empirical 1D CNN"],
        exclusion_criteria=["Animal studies"],
    )
    mock_pico = PICOQueryResult(
        population="Patients with cardiac arrhythmia",
        intervention="Lightweight 1D CNN",
        comparison="2D ResNet",
        outcome="F1-score and latency",
        search_keywords=["wearable ECG", "1D CNN", "arrhythmia"],
        boolean_query="",
    )

    with patch(
        "app.services.setup_agents.llm_router.generate_structured",
        new=AsyncMock(side_effect=[mock_scope, mock_criteria, mock_pico]),
    ) as mock_llm:
        res_scope = await run_scope_optimizer("1D CNN on wearable ECG")
        res_crit = await run_criteria_generator("1D CNN on wearable ECG")
        res_pico = await run_pico_query_generator("1D CNN on wearable ECG")

    assert mock_llm.call_count == 3
    assert res_scope.status == "optimal"
    assert len(res_crit.inclusion_criteria) == 2
    # Deterministic fallback fills boolean_query when LLM leaves it blank
    assert '"wearable ECG"' in res_pico.boolean_query
    assert "AND" in res_pico.boolean_query


@pytest.mark.asyncio
async def test_two_way_snowball_dedups_and_persists():
    proj_id = uuid.uuid4()
    seed_id = uuid.uuid4()
    project = ResearchProject(id=proj_id, owner_id=uuid.uuid4(), title="ECG SLR", research_question="Q")
    seed_paper = Paper(
        id=seed_id,
        project_id=proj_id,
        openalex_id="https://openalex.org/W100",
        title="Seed Paper",
    )

    mock_works = [
        ScholarlyWork(
            openalex_id="https://openalex.org/W101",
            doi="10.1000/back1",
            title="Backward Ref Paper",
            authors=["A. Author"],
            journal="IEEE Access",
            issn="2169-3536",
            year=2021,
            abstract="Ref abstract",
            citation_count=40,
            pdf_url=None,
            scopus_quartile="Q2",
            discovery_source="backward_snowball",
            seed_distance=1,
        ),
        ScholarlyWork(
            openalex_id="https://openalex.org/W102",
            doi="10.1000/fwd1",
            title="Forward Citing Paper",
            authors=["B. Author"],
            journal="Sensors",
            issn="1424-8220",
            year=2025,
            abstract="Fwd abstract",
            citation_count=12,
            pdf_url=None,
            scopus_quartile="Q2",
            discovery_source="forward_snowball",
            seed_distance=1,
        ),
        # Duplicate of already existing seed paper title should be skipped
        ScholarlyWork(
            openalex_id="https://openalex.org/W999",
            doi=None,
            title="Seed Paper",
            authors=[],
            journal=None,
            issn=None,
            year=2024,
            abstract=None,
            citation_count=5,
            pdf_url=None,
            discovery_source="forward_snowball",
            seed_distance=1,
        ),
    ]

    mock_db = AsyncMock()
    seed_res = MagicMock()
    seed_res.scalars.return_value.all.return_value = [seed_paper]
    existing_res = MagicMock()
    existing_res.all.return_value = [(None, "https://openalex.org/W100", "Seed Paper")]
    mock_db.execute = AsyncMock(side_effect=[seed_res, existing_res])
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch(
        "app.api.v1.search.run_two_way_snowball", new=AsyncMock(return_value=mock_works)
    ):
        resp = await snowball_papers(
            payload=SnowballRequest(seed_paper_ids=[seed_id], limit_per_direction=10, distance=1),
            project=project,
            db=mock_db,
        )

    assert resp.seeds_used == 1
    assert resp.added_count == 2
    assert resp.backward_count == 1
    assert resp.forward_count == 1


@pytest.mark.asyncio
async def test_run_two_way_snowball_merges_and_deduplicates():
    back = [
        ScholarlyWork(
            openalex_id="https://openalex.org/W2",
            doi="10.1/2",
            title="Ref A",
            authors=[],
            journal=None,
            issn=None,
            year=2020,
            abstract="a",
            citation_count=1,
            pdf_url=None,
            discovery_source="backward_snowball",
            seed_distance=1,
        )
    ]
    fwd = [
        ScholarlyWork(
            openalex_id="https://openalex.org/W2",
            doi="10.1/2",
            title="Ref A",
            authors=[],
            journal=None,
            issn=None,
            year=2020,
            abstract="a",
            citation_count=1,
            pdf_url=None,
            discovery_source="forward_snowball",
            seed_distance=1,
        ),
        ScholarlyWork(
            openalex_id="https://openalex.org/W3",
            doi="10.1/3",
            title="Citing B",
            authors=[],
            journal=None,
            issn=None,
            year=2025,
            abstract="b",
            citation_count=2,
            pdf_url=None,
            discovery_source="forward_snowball",
            seed_distance=1,
        ),
    ]
    with (
        patch("app.services.academic_search.fetch_backward_references", new=AsyncMock(return_value=back)),
        patch("app.services.academic_search.fetch_forward_citations", new=AsyncMock(return_value=fwd)),
    ):
        merged = await run_two_way_snowball(["https://openalex.org/W1"])

    assert len(merged) == 2
    assert {w.openalex_id for w in merged} == {"https://openalex.org/W2", "https://openalex.org/W3"}


@pytest.mark.asyncio
async def test_search_history_scoped_to_project():
    proj_id = uuid.uuid4()
    project = ResearchProject(id=proj_id, owner_id=uuid.uuid4(), title="Test", research_question="Q")
    q1 = SearchQuery(project_id=proj_id, query_string="wearable ECG", source_type="keyword", result_count=12)

    mock_db = AsyncMock()
    res = MagicMock()
    res.scalars.return_value.all.return_value = [q1]
    mock_db.execute = AsyncMock(return_value=res)

    history = await list_search_history(project=project, db=mock_db)
    assert len(history) == 1
    assert history[0].query_string == "wearable ECG"


def test_scimago_csv_parser_and_service():
    raw_csv = (
        'Rank;Sourceid;Title;Type;Issn;SJR;SJR Best Quartile;H index;Areas\n'
        '1;999;"Journal of TinyML Systems";journal;"12345678, 87654321";4,125;Q1;85;"Computer Science"\n'
        '2;1000;"Unranked Notes";journal;"00000000";0,100;-;3;"General"\n'
    )
    rows = parse_scimago_csv_text(raw_csv)
    assert len(rows) == 2
    assert rows[0]["issn"] == "1234-5678"
    assert rows[0]["sjr_score"] == 4.125
    assert rows[0]["quartile"] == "Q1"

    svc = SJRService(csv_path=Path("nonexistent_sjr.csv"))
    svc._csv_loaded = True
    for r in rows:
        svc._csv_issns[r["issn"]] = (r["quartile"], r["sjr_score"])
        svc._csv_titles[r["normalized_title"]] = (r["quartile"], r["sjr_score"])

    hit_by_issn = svc.lookup(issn="87654321", journal_title=None)
    assert hit_by_issn.quartile == "Q1"
    hit_by_title = svc.lookup(issn=None, journal_title="Journal of TinyML Systems")
    assert hit_by_title.quartile == "Q1"
