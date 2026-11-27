from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.llm_router import llm_router


class ExtractedClaimSchema(BaseModel):
    claim_text: str = Field(description="Core empirical or methodological claim made by the paper.")
    methodology: str = Field(description="Primary model, algorithm, or experimental design.")
    dataset: str = Field(description="Datasets or testbeds evaluated.")
    metric_summary: str = Field(description="Key quantitative findings (e.g., F1=0.92).")
    assumptions: list[str] = Field(
        default_factory=list, description="Explicit or implicit conditions."
    )
    evidence_quote: str = Field(description="Short verbatim snippet supporting this claim.")
    page_number: int | None = Field(
        default=None, description="Page number where evidence is found (if full-text)."
    )
    section_title: str | None = Field(
        default=None, description="Section heading containing the evidence (e.g., 'Results')."
    )


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
If [Page p.X | Section: ...] tags are present in the content, record the exact page_number (integer) and section_title where the evidence quote comes from.
Every "evidence_quote" MUST be a verbatim sentence/snippet copied from the Content below.

Title: {title}
Content/Excerpts:
{content[:9000]}
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
- Assumptions: {", ".join(claim_a.assumptions)}

[Paper B]: {paper_b_title}
- Claim: {claim_b.claim_text}
- Method: {claim_b.methodology}
- Dataset: {claim_b.dataset}
- Metrics: {claim_b.metric_summary}
- Assumptions: {", ".join(claim_b.assumptions)}

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


def select_candidate_conflict_pairs(
    claim_texts: list[str],
    paper_ids: list[str],
    top_k: int = 3,
    min_similarity: float = 0.08,
) -> list[tuple[int, int, float]]:
    """
    Given a list of claim representations and their originating paper IDs, computes TF-IDF cosine similarity
    and selects top-k candidate pairs across different papers.
    Reduces Agent 2 pairwise cross-examination complexity from O(N^2) to O(k * N).
    """
    n = len(claim_texts)
    if n < 2:
        return []

    # If very small number of claims, return all cross-paper pairs directly
    if n <= 3:
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                if paper_ids[i] != paper_ids[j]:
                    pairs.append((i, j, 1.0))
        return pairs

    # Fit TF-IDF on claim representations
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(claim_texts)
        sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    except Exception:
        # Fallback if vocabulary is empty or only stop words
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                if paper_ids[i] != paper_ids[j]:
                    pairs.append((i, j, 0.5))
        return pairs[: max(top_k * n, 5)]

    candidate_set: set[tuple[int, int]] = set()
    scored_pairs: list[tuple[int, int, float]] = []

    for i in range(n):
        candidates_for_i: list[tuple[int, float]] = []
        for j in range(n):
            if i != j and paper_ids[i] != paper_ids[j]:
                sim = float(sim_matrix[i, j])
                candidates_for_i.append((j, sim))

        candidates_for_i.sort(key=lambda x: x[1], reverse=True)

        picked = 0
        for j, sim in candidates_for_i:
            if sim >= min_similarity or picked == 0:
                pair_key = (min(i, j), max(i, j))
                if pair_key not in candidate_set:
                    candidate_set.add(pair_key)
                    scored_pairs.append((pair_key[0], pair_key[1], sim))
                picked += 1
                if picked >= top_k:
                    break

    scored_pairs.sort(key=lambda x: x[2], reverse=True)
    return scored_pairs

