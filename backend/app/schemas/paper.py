import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.paper import ScreeningSource, ScreeningStatus


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=30, ge=1, le=200)
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    open_access_only: bool = Field(default=False)


class SnowballRequest(BaseModel):
    seed_paper_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)
    limit_per_direction: int = Field(default=15, ge=1, le=50)
    distance: int = Field(default=1, ge=1, le=2)


class SearchQueryOut(BaseModel):
    id: uuid.UUID
    query_string: str
    source_type: str
    result_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperOut(BaseModel):
    id: uuid.UUID
    doi: str | None
    openalex_id: str | None = None
    title: str
    authors: list[str]
    journal: str | None
    year: int | None
    abstract: str | None
    citation_count: int
    pdf_url: str | None = None
    scopus_quartile: str | None
    discovery_source: str = "keyword"
    seed_distance: int = 0
    screening_status: ScreeningStatus
    screening_source: ScreeningSource
    al_inclusion_prob: float | None
    al_uncertainty_score: float | None

    model_config = {"from_attributes": True}


class SnowballResponse(BaseModel):
    seeds_used: int
    added_count: int
    backward_count: int
    forward_count: int
    papers: list[PaperOut]


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
