from pydantic import BaseModel, Field

from app.services.llm_router import llm_router


class ExtractedClaimSchema(BaseModel):
    claim_text: str = Field(description="Core empirical or methodological claim made by the paper.")
    methodology: str = Field(description="Primary model, algorithm, or experimental design.")
    dataset: str = Field(description="Datasets or testbeds evaluated.")
    metric_summary: str = Field(description="Key quantitative findings (e.g., F1=0.92).")
    assumptions: list[str] = Field(default_factory=list, description="Explicit or implicit conditions.")
    evidence_quote: str = Field(description="Short verbatim snippet supporting this claim.")


class PaperClaimsOutput(BaseModel):
    claims: list[ExtractedClaimSchema]


class CrossExaminationOutput(BaseModel):
    relation_type: str = Field(
        description="One of: contradicts, supports, refines, assumption_mismatch"
    )
    confidence: float = Field(ge=0.0, le=1.0)
    debate_summary: str = Field(
        description="Structured debate comparing Paper A's Advocate vs Paper B's Challenger."
    )
    root_cause_hypothesis: str = Field(
        description="Why these two claims agree or conflict (dataset, noise, assumptions)."
    )


class SynthesizedGapItem(BaseModel):
    title: str
    description: str
    suggested_direction: str
    novelty_score: float = Field(ge=0.0, le=1.0)


class GapSynthesisOutput(BaseModel):
    gaps: list[SynthesizedGapItem]


async def extract_paper_claims(title: str, content: str) -> PaperClaimsOutput:
    prompt = f"""
Analyze the following scientific paper and extract 1-3 concrete, verifiable claims.

Title: {title}
Content/Abstract:
{content[:6000]}
"""
    return await llm_router.generate_structured(
        prompt=prompt,
        schema=PaperClaimsOutput,
        system_prompt="You are Agent 1 (Claim Extractor). Extract structured scientific claims accurately without hallucination.",
        temperature=0.1,
    )


async def cross_examine_claims(
    paper_a_title: str,
    claim_a: ExtractedClaimSchema,
    paper_b_title: str,
    claim_b: ExtractedClaimSchema,
) -> CrossExaminationOutput:
    prompt = f"""
Act as a Cross-Examiner moderating a scientific debate between two papers:

[Paper A]: {paper_a_title}
- Claim: {claim_a.claim_text}
- Method: {claim_a.methodology}
- Dataset: {claim_a.dataset}
- Metrics: {claim_a.metric_summary}
- Assumptions: {', '.join(claim_a.assumptions)}

[Paper B]: {paper_b_title}
- Claim: {claim_b.claim_text}
- Method: {claim_b.methodology}
- Dataset: {claim_b.dataset}
- Metrics: {claim_b.metric_summary}
- Assumptions: {', '.join(claim_b.assumptions)}

Determine whether Paper B contradicts, supports, refines, or has an assumption_mismatch with Paper A.
Explain the root cause (e.g., domain shift, hardware limits, dataset bias).
"""
    return await llm_router.generate_structured(
        prompt=prompt,
        schema=CrossExaminationOutput,
        system_prompt="You are Agent 2 (Cross-Examiner). Identify real academic conflicts and assumption mismatches.",
        temperature=0.2,
    )


async def synthesize_research_gaps(
    research_question: str,
    conflict_summaries: list[str],
) -> GapSynthesisOutput:
    formatted_conflicts = "\n".join(f"- {c}" for c in conflict_summaries)
    prompt = f"""
Research Question: {research_question}

Cross-Paper Conflicts & Assumption Mismatches Discovered:
{formatted_conflicts}

Synthesize the top 3 concrete, publishable Research Gaps and propose experimental directions to resolve these conflicts.
"""
    return await llm_router.generate_structured(
        prompt=prompt,
        schema=GapSynthesisOutput,
        system_prompt="You are Agent 3 (Research Gap Synthesizer). Turn cross-paper conflicts into novel research hypotheses.",
        temperature=0.3,
    )
