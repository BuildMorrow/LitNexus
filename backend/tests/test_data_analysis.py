"""Test suite for Data Profiling, Statistical Warning Guards, and Method Advisory."""

import uuid
import pytest

from app.models.dataset import RiskLevel
from app.models.project import ResearchProject
from app.schemas.dataset import ColumnMeta
from app.services.data_profiler import data_profiler
from app.services.data_analysis_advisor import data_analysis_advisor


def test_parse_and_profile_csv():
    csv_text = """subject_id,age,hrv_rmssd,arrhythmia_label
sub_01,45,34.2,1
sub_02,52,28.5,0
sub_03,38,,1
sub_04,61,42.1,0
"""
    row_count, col_count, cols_meta, missing_summary, preview = (
        data_profiler.parse_and_profile_csv(csv_text)
    )

    assert row_count == 4
    assert col_count == 4
    assert missing_summary["hrv_rmssd"] == 1
    assert len(preview) == 4

    meta_dict = {c.name: c for c in cols_meta}
    assert meta_dict["age"].data_type == "numeric"
    assert meta_dict["hrv_rmssd"].missing_ratio == 0.25


def test_inspect_limitations_flags_small_sample_size():
    # N = 15 (< 30) should trigger high risk and small sample size warning
    dummy_cols = [
        ColumnMeta(name="f1", data_type="numeric", missing_count=0, missing_ratio=0.0, unique_count=15)
    ]
    risk, warnings = data_profiler.inspect_limitations(row_count=15, columns_meta=dummy_cols)

    assert risk == RiskLevel.high
    types = [w.warning_type for w in warnings]
    assert "SMALL_SAMPLE_SIZE" in types
    # Must recommend non-parametric tests
    assert any("non-parametric" in w.recommendation.lower() for w in warnings)


@pytest.mark.asyncio
async def test_data_analysis_advisor_fallback():
    dummy_cols = [
        ColumnMeta(name="sensitivity", data_type="numeric", missing_count=0, missing_ratio=0.0, unique_count=20),
        ColumnMeta(name="device_group", data_type="string", missing_count=0, missing_ratio=0.0, unique_count=2),
    ]
    methods, code, guide, warnings = await data_analysis_advisor.advise_methods(
        research_question="Does sensor sensitivity differ by device group?",
        analysis_goal="Compare sensitivity between Group A and Group B",
        row_count=25,
        columns_meta=dummy_cols,
        rule_warnings=[],
        risk_level=RiskLevel.high,
    )

    assert len(methods) >= 1
    assert "pandas" in code
    assert len(guide) > 0
