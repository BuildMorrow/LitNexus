import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
from app.services.code_sandbox import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    code_sandbox,
)
from app.services.data_analysis_advisor import data_analysis_advisor
from app.services.data_profiler import data_profiler

router = APIRouter(prefix="/projects/{project_id}/analysis", tags=["data-analysis"])


async def _profile_and_save_dataset(
    db: AsyncSession,
    project: ResearchProject,
    *,
    dataset_name: str,
    description: str | None,
    csv_raw_text: str,
) -> DatasetProfileOut:
    try:
        row_count, col_count, cols_meta, missing_summary, preview = (
            data_profiler.parse_and_profile_csv(csv_raw_text)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {exc}",
        ) from exc

    dataset_profile = DatasetProfile(
        project_id=project.id,
        dataset_name=dataset_name,
        description=description,
        row_count=row_count,
        column_count=col_count,
        columns_metadata=[c.model_dump() for c in cols_meta],
        missing_value_summary=missing_summary,
        sample_preview=preview,
        raw_csv_text=csv_raw_text,
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


@router.post("/datasets", response_model=DatasetProfileOut, status_code=status.HTTP_201_CREATED)
async def upload_and_profile_dataset(
    payload: DatasetIngestRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Profile raw CSV text for initial exploratory data analysis."""
    return await _profile_and_save_dataset(
        db,
        project,
        dataset_name=payload.dataset_name,
        description=payload.description,
        csv_raw_text=payload.csv_raw_text,
    )


@router.post("/datasets/upload-file", response_model=DatasetProfileOut, status_code=status.HTTP_201_CREATED)
async def upload_csv_file_dataset(
    file: UploadFile = File(...),
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Upload a local CSV file, profile schema/missingness, and store for sandbox execution."""
    raw_bytes = await file.read()
    if not raw_bytes or len(raw_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CSV file is empty or exceeds 10MB limit.")
    csv_text = raw_bytes.decode("utf-8-sig", errors="replace")
    return await _profile_and_save_dataset(
        db,
        project,
        dataset_name=file.filename or "uploaded_dataset.csv",
        description="Uploaded CSV file",
        csv_raw_text=csv_text,
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
    """Recommend statistical/ML methods, generate Python code, and enforce data limitation warnings."""
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
    risk_level, rule_warnings = data_profiler.inspect_limitations(
        row_count=dataset.row_count,
        columns_meta=cols_meta,
    )

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


@router.post("/datasets/{dataset_id}/execute", response_model=CodeExecutionResponse)
async def execute_dataset_sandbox_code(
    dataset_id: uuid.UUID,
    payload: CodeExecutionRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Execute Python EDA code inside an AST-guarded isolated sandbox with dataset preloaded as `df`."""
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

    csv_text = dataset.raw_csv_text or ""
    return await code_sandbox.execute_code_async(
        code=payload.code,
        csv_text=csv_text,
        timeout_seconds=payload.timeout_seconds,
    )
