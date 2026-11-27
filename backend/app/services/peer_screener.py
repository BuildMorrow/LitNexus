"""Dual-Agent Peer Screener (Inclusive vs. Strict + Adjudicator).

Only evaluates borderline uncertain papers after Active Learning filtering.
Every evidence quote is verified deterministically via grounding_verifier.
"""

import asyncio
from typing import Literal

from pydantic import BaseModel, Field

from app.services.grounding_verifier import verify_quotes
from app.services.llm_router import llm_router


class PeerReviewerOutput(BaseModel):
    decision: Literal["included", "excluded", "uncertain"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Concise rationale referencing inclusion/exclusion rules.")
    matches: list[str] = Field(default_factory=list, description="Criteria satisfied.")
    mismatches: list[str] = Field(default_factory=list, description="Criteria violated or unclear.")
    evidence_quotes: list[str] = Field(
        default_factory=list,
        description="Exact verbatim sentences copied from Title/Abstract/Full-text proving the decision.",
    )


class ReviewerOpinionRecord(BaseModel):
    reviewer_role: Literal["inclusive", "strict", "adjudicator"]
    decision: Literal["included", "excluded", "uncertain"]
    confidence: float
    reason: str
    matches: list[str] = Field(default_factory=list)
    mismatches: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)


class PeerScreeningVerdict(BaseModel):
    paper_id: str
    final_decision: Literal["included", "excluded", "uncertain"]
    confidence: float
    disagreed: bool
    grounding_score: float
    verified_quotes: list[str] = Field(default_factory=list)
    opinions: list[ReviewerOpinionRecord] = Field(default_factory=list)
    final_reason: str


_STANCES = {
    "inclusive": (
        "You are Reviewer 1 (INCLUSIVE stance). Prioritize HIGH RECALL: do not accidentally drop relevant papers. "
        "Only exclude if the paper clearly violates exclusion criteria or is off-topic."
    ),
    "strict": (
        "You are Reviewer 2 (STRICT stance). Prioritize HIGH PRECISION: only include if the paper rigorously "
        "satisfies ALL inclusion criteria with concrete empirical methodology."
    ),
    "adjudicator": (
        "You are Reviewer 3 (INDEPENDENT ADJUDICATOR). Reviewers 1 and 2 disagreed. "
        "Resolve the disagreement strictly according to the PRISMA inclusion/exclusion rules and verbatim evidence."
    ),
}


async def _ask_reviewer(
    *,
    role: Literal["inclusive", "strict", "adjudicator"],
    research_question: str,
    inclusion_criteria: list[str],
    exclusion_criteria: list[str],
    title: str,
    abstract: str,
    extra_debate_context: str = "",
) -> PeerReviewerOutput:
    inc_text = "\n".join(f"- {c}" for c in inclusion_criteria) or "- None specified"
    exc_text = "\n".join(f"- {c}" for c in exclusion_criteria) or "- None specified"

    prompt = f"""
{_STANCES[role]}

[Research Question]: {research_question}
[Inclusion Criteria]:
{inc_text}

[Exclusion Criteria]:
{exc_text}

[Candidate Paper]:
- Title: {title}
- Abstract / Excerpts: {abstract}
{extra_debate_context}

CRITICAL: All strings in "evidence_quotes" MUST be exact verbatim substrings copied from the Candidate Paper text above.
"""
    return await llm_router.generate_structured(
        prompt=prompt,
        schema=PeerReviewerOutput,
        system_prompt="You are a rigorous PRISMA peer reviewer. Output valid JSON strictly matching the schema.",
        temperature=0.1,
    )


async def dual_peer_screen_paper(
    *,
    paper_id: str,
    title: str,
    abstract: str,
    segments: list[tuple[str, int | None]],
    research_question: str,
    inclusion_criteria: list[str],
    exclusion_criteria: list[str],
) -> PeerScreeningVerdict:
    """Run blind parallel inclusive & strict reviews, escalating to adjudicator only on disagreement."""
    content_text = abstract or title
    op_inc, op_str = await asyncio.gather(
        _ask_reviewer(
            role="inclusive",
            research_question=research_question,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            title=title,
            abstract=content_text,
        ),
        _ask_reviewer(
            role="strict",
            research_question=research_question,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            title=title,
            abstract=content_text,
        ),
    )

    opinions: list[ReviewerOpinionRecord] = [
        ReviewerOpinionRecord(
            reviewer_role="inclusive",
            decision=op_inc.decision,
            confidence=op_inc.confidence,
            reason=op_inc.reason,
            matches=op_inc.matches,
            mismatches=op_inc.mismatches,
            evidence_quotes=op_inc.evidence_quotes,
        ),
        ReviewerOpinionRecord(
            reviewer_role="strict",
            decision=op_str.decision,
            confidence=op_str.confidence,
            reason=op_str.reason,
            matches=op_str.matches,
            mismatches=op_str.mismatches,
            evidence_quotes=op_str.evidence_quotes,
        ),
    ]

    all_quotes = list(dict.fromkeys([*op_inc.evidence_quotes, *op_str.evidence_quotes]))
    disagreed = op_inc.decision != op_str.decision

    if disagreed:
        debate_ctx = (
            f"\n[Disagreement Summary]:\n"
            f"- Inclusive Reviewer ({op_inc.decision}, conf={op_inc.confidence:.2f}): {op_inc.reason}\n"
            f"- Strict Reviewer ({op_str.decision}, conf={op_str.confidence:.2f}): {op_str.reason}\n"
        )
        op_adj = await _ask_reviewer(
            role="adjudicator",
            research_question=research_question,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            title=title,
            abstract=content_text,
            extra_debate_context=debate_ctx,
        )
        opinions.append(
            ReviewerOpinionRecord(
                reviewer_role="adjudicator",
                decision=op_adj.decision,
                confidence=op_adj.confidence,
                reason=op_adj.reason,
                matches=op_adj.matches,
                mismatches=op_adj.mismatches,
                evidence_quotes=op_adj.evidence_quotes,
            )
        )
        all_quotes = list(dict.fromkeys([*all_quotes, *op_adj.evidence_quotes]))
        final_decision = op_adj.decision
        final_conf = op_adj.confidence
        final_reason = op_adj.reason
    else:
        winner = op_inc if op_inc.confidence >= op_str.confidence else op_str
        final_decision = winner.decision
        final_conf = round((op_inc.confidence + op_str.confidence) / 2.0, 4)
        final_reason = winner.reason

    verified_matches, grounding_score = verify_quotes(all_quotes, segments)
    return PeerScreeningVerdict(
        paper_id=paper_id,
        final_decision=final_decision,
        confidence=final_conf,
        disagreed=disagreed,
        grounding_score=grounding_score,
        verified_quotes=[m.quote for m in verified_matches],
        opinions=opinions,
        final_reason=final_reason,
    )
