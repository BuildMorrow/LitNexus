import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.dataset import AnalysisSession, DatasetProfile
from app.models.project import ResearchProject
from app.schemas.dataset import (
    AnalysisAdviceRequest,
    AnalysisAdviceResponse,
    ColumnMeta,
    DatasetIngestRequest,
    DatasetProfileOut,
)
from app.services.data_analysis_advisor import data_analysis_advisor
from app.services.data_profiler import data_profiler

router = APIRouter(prefix="/projects/{project_id}/analysis", tags=["data-analysis"])


@router.post("/datasets", response_model=DatasetProfileOut, status_code=status.HTTP_201_CREATED)
async def upload_and_profile_dataset(
    payload: DatasetIngestRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and profile an empirical dataset (CSV) for initial exploratory data analysis.
    Extracts column metadata, data types, missing value ratios, and sample preview.
    """
    try:
        row_count, col_count, cols_meta, missing_summary, preview = (
            data_profiler.parse_and_profile_csv(payload.csv_raw_text)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {exc}",
        ) from exc

    dataset_profile = DatasetProfile(
        project_id=project.id,
        dataset_name=payload.dataset_name,
        description=payload.description,
        row_count=row_count,
        column_count=col_count,
        columns_metadata=[c.model_dump() for c in cols_meta],
        missing_value_summary=missing_summary,
        sample_preview=preview,
    )

    db.add(dataset_profile)
    await db.commit()
    await db.refresh(dataset_profile)

    return DatasetProfileOut(
        id=dataset_profile.id,
        project_id=dataset_profile.project_id,
        dataset_name=dataset_profile.dataset_name,
        description=dataset_profile.description,
        row_count=dataset_profile.row_count,
        column_count=dataset_profile.column_count,
        columns_metadata=[ColumnMeta(**c) for c in dataset_profile.columns_metadata],
        missing_value_summary=dataset_profile.missing_value_summary,
        sample_preview=dataset_profile.sample_preview,
        created_at=dataset_profile.created_at,
    )


@router.get("/datasets", response_model=list[DatasetProfileOut])
async def list_project_datasets(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DatasetProfile)
        .where(DatasetProfile.project_id == project.id)
        .order_by(DatasetProfile.created_at.desc())
    )
    records = list(result.scalars().all())
    return [
        DatasetProfileOut(
            id=d.id,
            project_id=d.project_id,
            dataset_name=d.dataset_name,
            description=d.description,
            row_count=d.row_count,
            column_count=d.column_count,
            columns_metadata=[ColumnMeta(**c) for c in d.columns_metadata],
            missing_value_summary=d.missing_value_summary,
            sample_preview=d.sample_preview,
            created_at=d.created_at,
        )
        for d in records
    ]


@router.post("/datasets/{dataset_id}/advise", response_model=AnalysisAdviceResponse)
async def advise_data_analysis(
    dataset_id: uuid.UUID,
    payload: AnalysisAdviceRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """
    Recommend appropriate statistical/ML analysis methods, generate executable Python code,
    and formulate interpretation guidelines with rigorous warnings on data limitations (N < 30, imbalance, missingness).
    """
    result = await db.execute(
        select(DatasetProfile).where(
            DatasetProfile.id == dataset_id,
            DatasetProfile.project_id == project.id,
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset profile not found in project.",
        )

    cols_meta = [ColumnMeta(**c) for c in dataset.columns_metadata]

    # Rule-based limitation inspection
    risk_level, rule_warnings = data_profiler.inspect_limitations(
        row_count=dataset.row_count,
        columns_meta=cols_meta,
    )

    # Advisor synthesizes methodology and executable code
    (
        recommended_methods,
        code,
        interpretation,
        combined_warnings,
    ) = await data_analysis_advisor.advise_methods(
        research_question=project.research_question,
        analysis_goal=payload.analysis_goal,
        row_count=dataset.row_count,
        columns_meta=cols_meta,
        rule_warnings=rule_warnings,
        risk_level=risk_level,
    )

    # Persist session
    session_record = AnalysisSession(
        project_id=project.id,
        dataset_id=dataset.id,
        analysis_goal=payload.analysis_goal,
        recommended_methods=[m.model_dump() for m in recommended_methods],
        selected_method=recommended_methods[0].method_name if recommended_methods else None,
        generated_code=code,
        data_limitations=[w.model_dump() for w in combined_warnings],
        risk_level=risk_level,
        interpretation=interpretation,
    )
    db.add(session_record)
    await db.commit()

    return AnalysisAdviceResponse(
        dataset_id=dataset.id,
        analysis_goal=payload.analysis_goal,
        risk_level=risk_level,
        recommended_methods=recommended_methods,
        data_limitations=combined_warnings,
        suggested_python_code=code,
        interpretation_guide=interpretation,
    )
