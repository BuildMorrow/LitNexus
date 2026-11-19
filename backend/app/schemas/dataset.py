import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.dataset import RiskLevel


class ColumnMeta(BaseModel):
    name: str
    data_type: str
    missing_count: int = 0
    missing_ratio: float = 0.0
    unique_count: int = 0
    sample_values: list = Field(default_factory=list)


class DatasetIngestRequest(BaseModel):
    dataset_name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    csv_raw_text: str = Field(description="Raw CSV text content uploaded or pasted by user.")


class DatasetProfileOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_name: str
    description: str | None
    row_count: int
    column_count: int
    columns_metadata: list[ColumnMeta]
    missing_value_summary: dict
    sample_preview: list[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisMethodProposal(BaseModel):
    method_name: str = Field(description="e.g., Logistic Regression, Two-Sample T-test, Mann-Whitney U, Random Forest")
    category: str = Field(description="e.g., Parametric Hypothesis Testing, Non-parametric, Supervised ML")
    rational: str = Field(description="Why this method fits the research question and data schema")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions required (e.g., normality, N>=30)")
    is_recommended: bool = True


class DataLimitationWarning(BaseModel):
    warning_type: str = Field(description="e.g., SMALL_SAMPLE_SIZE, CLASS_IMBALANCE, HIGH_MISSINGNESS, SKEWED_DISTRIBUTION")
    severity: RiskLevel
    message: str = Field(description="Actionable warning explaining statistical risk")
    recommendation: str = Field(description="How to mitigate or guard against false discovery")


class AnalysisAdviceRequest(BaseModel):
    analysis_goal: str = Field(description="e.g., Test if wearable ECG algorithm differs in sensitivity across age groups")
    target_column: str | None = None


class AnalysisAdviceResponse(BaseModel):
    dataset_id: uuid.UUID
    analysis_goal: str
    risk_level: RiskLevel
    recommended_methods: list[AnalysisMethodProposal]
    data_limitations: list[DataLimitationWarning]
    suggested_python_code: str
    interpretation_guide: str
