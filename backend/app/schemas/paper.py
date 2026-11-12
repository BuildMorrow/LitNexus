import uuid

from pydantic import BaseModel, Field

from app.models.paper import ScreeningSource, ScreeningStatus


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=30, ge=1, le=200)


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


class ActiveLearningSummary(BaseModel):
    total_papers: int
    labeled_count: int
    auto_included: int
    auto_excluded: int
    needs_review: int
