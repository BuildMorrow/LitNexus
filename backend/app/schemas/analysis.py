import uuid

from pydantic import BaseModel

from app.models.conflict import EdgeRelationType


class ConflictEdgeOut(BaseModel):
    id: uuid.UUID
    source_claim_id: uuid.UUID
    target_claim_id: uuid.UUID
    relation_type: EdgeRelationType
    confidence: float
    debate_summary: str
    root_cause_hypothesis: str | None

    model_config = {"from_attributes": True}


class ResearchGapOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    suggested_direction: str | None
    novelty_score: float

    model_config = {"from_attributes": True}


class ConflictAnalysisOut(BaseModel):
    claims_extracted: int
    edges_discovered: list[ConflictEdgeOut]
    research_gaps: list[ResearchGapOut]
