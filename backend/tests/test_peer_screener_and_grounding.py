"""Tests for Sprint C: Deterministic Grounding Verifier, Dual-Agent Peer Screener & Quality Gate."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.screening import compute_project_quality_gate
from app.models.paper import Paper, ScreeningSource, ScreeningStatus
from app.services.grounding_verifier import verify_quotes
from app.services.peer_screener import PeerReviewerOutput, dual_peer_screen_paper


def test_grounding_verifier_catches_fabricated_quotes():
    segments = [
        (
            "Our 1D CNN achieves 98.2% F1-score on the MIT-BIH dataset with 18ms latency on Cortex-M4.",
            2,
        )
    ]
    real_quote = "1D CNN achieves 98.2% F1-score on the MIT-BIH dataset"
    fabricated_quote = "Quantum transformers reached 99.9% accuracy on astrophysics telemetry."

    matches, score = verify_quotes([real_quote, fabricated_quote], segments)
    assert len(matches) == 1
    assert matches[0].page_number == 2
    assert matches[0].score == 1.0
    assert score == 0.5


@pytest.mark.asyncio
async def test_dual_peer_screener_no_disagreement_skips_adjudicator():
    op_inc = PeerReviewerOutput(
        decision="included",
        confidence=0.90,
        reason="Matches 1D CNN wearable ECG criteria.",
        matches=["Uses 1D CNN", "Wearable ECG"],
        mismatches=[],
        evidence_quotes=["We propose a 1D CNN on single-lead wearable ECG patches."],
    )
    op_str = PeerReviewerOutput(
        decision="included",
        confidence=0.84,
        reason="Empirical benchmark clearly reported.",
        matches=["Empirical metrics"],
        mismatches=[],
        evidence_quotes=["achieves 97.5% F1 on ambulatory ECG recordings."],
    )

    with patch(
        "app.services.peer_screener.llm_router.generate_structured",
        new=AsyncMock(side_effect=[op_inc, op_str]),
    ) as mock_llm:
        verdict = await dual_peer_screen_paper(
            paper_id="p1",
            title="Wearable 1D CNN",
            abstract="We propose a 1D CNN on single-lead wearable ECG patches and achieves 97.5% F1 on ambulatory ECG recordings.",
            segments=[
                (
                    "We propose a 1D CNN on single-lead wearable ECG patches and achieves 97.5% F1 on ambulatory ECG recordings.",
                    1,
                )
            ],
            research_question="How effective are 1D CNNs?",
            inclusion_criteria=["1D CNN", "Wearable ECG"],
            exclusion_criteria=["Animal study"],
        )

    assert mock_llm.call_count == 2  # Adjudicator was NOT called
    assert verdict.disagreed is False
    assert verdict.final_decision == "included"
    assert verdict.grounding_score == 1.0
    assert len(verdict.opinions) == 2


@pytest.mark.asyncio
async def test_dual_peer_screener_escalates_disagreement_to_adjudicator():
    op_inc = PeerReviewerOutput(
        decision="included",
        confidence=0.72,
        reason="Relevant wearable telemetry method.",
        evidence_quotes=["wearable telemetry patch"],
    )
    op_str = PeerReviewerOutput(
        decision="excluded",
        confidence=0.88,
        reason="Evaluated on 12-lead hospital ECG only.",
        evidence_quotes=["12-lead hospital telemetry"],
    )
    op_adj = PeerReviewerOutput(
        decision="excluded",
        confidence=0.93,
        reason="Exclusion rule explicitly rejects 12-lead clinical ECG.",
        evidence_quotes=["12-lead hospital telemetry"],
    )

    with patch(
        "app.services.peer_screener.llm_router.generate_structured",
        new=AsyncMock(side_effect=[op_inc, op_str, op_adj]),
    ) as mock_llm:
        verdict = await dual_peer_screen_paper(
            paper_id="p2",
            title="Hospital 12-lead ECG telemetry",
            abstract="Uses a wearable telemetry patch with 12-lead hospital telemetry monitoring.",
            segments=[("Uses a wearable telemetry patch with 12-lead hospital telemetry monitoring.", None)],
            research_question="Single-lead wearable ECG?",
            inclusion_criteria=["Single-lead ECG"],
            exclusion_criteria=["12-lead clinical ECG"],
        )

    assert mock_llm.call_count == 3  # Adjudicator WAS called
    assert verdict.disagreed is True
    assert verdict.final_decision == "excluded"
    assert len(verdict.opinions) == 3
    assert verdict.opinions[2].reviewer_role == "adjudicator"


def test_quality_gate_blocks_low_grounding_or_small_corpus():
    p1 = Paper(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Paper 1",
        abstract="Exact text on MIT-BIH.",
        screening_status=ScreeningStatus.included,
        screening_source=ScreeningSource.llm,
        screening_rationale={"grounding_score": 1.0},
    )
    p2 = Paper(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Paper 2",
        abstract="Exact text on hardware.",
        screening_status=ScreeningStatus.included,
        screening_source=ScreeningSource.llm,
        screening_rationale={"grounding_score": 0.2},
    )
    gate = compute_project_quality_gate([p1, p2], grounding_threshold=0.80, min_papers=3)
    assert gate.passed is False
    assert gate.requires_hitl_review is True
    assert gate.grounding_precision == 0.6
    assert len(gate.warnings) == 2

    # When HITL approves + corpus reaches 3 papers -> Gate passes
    p2.screening_rationale = {"hitl_approved": True}
    p3 = Paper(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Paper 3",
        abstract="Clean ECG benchmark.",
        screening_status=ScreeningStatus.included,
        screening_source=ScreeningSource.human,
        screening_rationale={"hitl_approved": True},
    )
    gate_ok = compute_project_quality_gate([p1, p2, p3], grounding_threshold=0.80, min_papers=3)
    assert gate_ok.passed is True
    assert gate_ok.grounding_precision == 1.0
