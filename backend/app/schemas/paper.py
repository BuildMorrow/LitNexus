import uuid

from pydantic import BaseModel, Field

from app.models.paper import ScreeningSource, ScreeningStatus


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=30, ge=1, le=200)
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    open_access_only: bool = Field(default=False)


class PaperOut(BaseModel):
    id: uuid.UUID
    doi: str | None
    title: str
    authors: list[str]
    journal: str | None
    year: int | None
    abstract: str | None
    citation_count: int
    scopus_quartile: str | None
    screening_status: ScreeningStatus
    screening_source: ScreeningSource
    al_inclusion_prob: float | None
    al_uncertainty_score: float | None

    model_config = {"from_attributes": True}


class PaperLabelRequest(BaseModel):
    status: ScreeningStatus
    reason: str | None = None


class LLMBatchScreenRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)


class LLMScreeningDecision(BaseModel):
    paper_id: str
    status: ScreeningStatus
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Clear academic rationale for inclusion or exclusion.")
    evidence_quote: str = Field(
        description="Verbatim sentence or snippet from title/abstract grounding this decision."
    )


class LLMBatchScreenResponse(BaseModel):
    processed_count: int
    auto_included: int
    auto_excluded: int
    decisions: list[LLMScreeningDecision]


class ActiveLearningSummary(BaseModel):
    total_papers: int
    labeled_count: int
    auto_included: int
    auto_excluded: int
    needs_review: int
