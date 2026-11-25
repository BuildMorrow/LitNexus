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


class ConflictGraphNode(BaseModel):
    id: str
    type: str  # "paper" or "claim"
    label: str
    paper_title: str
    year: int | None = None
    quartile: str | None = None
    details: str | None = None


class ConflictGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: EdgeRelationType
    confidence: float
    debate_summary: str
    root_cause_hypothesis: str | None = None


class ConflictGraphResponse(BaseModel):
    total_nodes: int
    total_edges: int
    contradiction_count: int
    nodes: list[ConflictGraphNode]
    edges: list[ConflictGraphEdge]
    research_gaps: list[ResearchGapOut]


class DraftReportResponse(BaseModel):
    project_id: uuid.UUID
    project_title: str
    draft_markdown: str
    bibtex_content: str
    prisma_flow_summary: dict
    total_references: int


class ComparativeMatrixItem(BaseModel):
    paper_id: uuid.UUID
    paper_title: str
    year: int | None
    scopus_quartile: str | None
    claim_id: uuid.UUID
    claim_text: str
    methodology: str
    dataset: str
    metric_summary: str
    assumptions: list[str]
    evidence_quote: str
    page_number: int | None = None
    section_title: str | None = None


class ComparativeMatrixResponse(BaseModel):
    total_papers: int
    total_claims: int
    items: list[ComparativeMatrixItem]


class KPIMetricsResponse(BaseModel):
    total_papers: int
    included_count: int
    excluded_count: int
    uncertain_count: int
    unscreened_count: int
    human_labeled: int
    llm_labeled: int
    active_learning_labeled: int
    automation_rate: float  # Percentage of papers screened automatically by AL or LLM
    token_savings_percentage: float  # Estimated token cost saved compared to reading all papers
    estimated_hours_saved: float  # Assuming 15 minutes manual reading per paper
