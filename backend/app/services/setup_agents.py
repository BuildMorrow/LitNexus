"""AI Research Setup Agents (Scope Optimizer, Criteria Generator, PICO & Boolean Query).

All LLM calls go strictly through llm_router.generate_structured() with Pydantic schemas.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.services.llm_router import llm_router


class ScopeAnalysisResult(BaseModel):
    status: Literal["too_broad", "optimal", "too_narrow"] = Field(
        description="Scope evaluation verdict."
    )
    score: int = Field(ge=0, le=100, description="Scope optimality score from 0 to 100.")
    feedback: str = Field(description="Concise academic feedback explaining scope strengths or gaps.")
    suggested_topics: list[str] = Field(
        default_factory=list,
        description="2-3 refined academic research questions tailored to the user's topic.",
    )


class CriteriaGenerationResult(BaseModel):
    inclusion_criteria: list[str] = Field(
        default_factory=list, description="3-4 rigorous PRISMA inclusion rules."
    )
    exclusion_criteria: list[str] = Field(
        default_factory=list, description="3-4 rigorous PRISMA exclusion rules."
    )


class PICOQueryResult(BaseModel):
    population: str = Field(description="Target population, problem, or system domain in English.")
    intervention: str = Field(description="Primary method, model, or intervention in English.")
    comparison: str = Field(default="N/A", description="Baseline or comparator method in English.")
    outcome: str = Field(description="Measured quantitative metrics or clinical/engineering outcomes.")
    search_keywords: list[str] = Field(
        default_factory=list, description="5-8 precise English academic search keywords."
    )
    boolean_query: str = Field(
        description="Ready-to-run Boolean query with AND/OR operators and quoted multi-word terms."
    )


def build_boolean_query(population: str, intervention: str, keywords: list[str]) -> str:
    """Deterministic fallback query builder if LLM omits boolean_query formatting."""
    clean_kw = [f'"{kw.strip()}"' if " " in kw.strip() else kw.strip() for kw in keywords if kw.strip()]
    if len(clean_kw) >= 2:
        core = " AND ".join(clean_kw[:2])
        if len(clean_kw) > 2:
            tail = " OR ".join(clean_kw[2:5])
            return f"({core}) AND ({tail})"
        return core
    parts = [p.strip() for p in (population, intervention) if p and p.strip()]
    return " AND ".join(f'"{p}"' if " " in p else p for p in parts)


async def run_scope_optimizer(idea: str, research_field: str = "") -> ScopeAnalysisResult:
    """Evaluate research scope width and suggest refined academic research questions."""
    prompt = f"""
Act as an Academic Research Methodology Advisor. Evaluate the scope of this research idea:
- Topic / Research Question: "{idea.strip()}"
- Domain / Field: "{research_field.strip() or 'Computer Science / Biomedical AI'}"

Classify status strictly into one of:
- "too_broad": Generic technology + broad domain with no specific problem, target cohort, or evaluation goal.
- "optimal": Specific method/model + defined system/population + clear evaluation/comparison objective.
- "too_narrow": Locked into one isolated institution, single class, or overly narrow timeframe that prevents finding international literature.

Provide a 0-100 optimality score, concise feedback (in Vietnamese if the input is Vietnamese, otherwise English), and 2-3 sharpened research questions in the same language as the topic.
"""
    return await llm_router.generate_structured(
        prompt=prompt,
        schema=ScopeAnalysisResult,
        system_prompt="You are Agent 1 (Scope Optimizer). Return valid JSON strictly matching the schema.",
        temperature=0.0,
    )


async def run_criteria_generator(idea: str, research_field: str = "") -> CriteriaGenerationResult:
    """Generate PRISMA 2020 aligned inclusion and exclusion criteria for the research topic."""
    prompt = f"""
Act as a Systematic Literature Review (PRISMA 2020) Expert.
Research Topic: "{idea.strip()}"
Domain: "{research_field.strip() or 'Computer Science / Engineering'}"

Generate:
1. "inclusion_criteria": 3-4 concrete inclusion criteria (publication recency, empirical evaluation/dataset requirements, peer-reviewed English articles).
2. "exclusion_criteria": 3-4 strict exclusion criteria (short abstracts < 3 pages, non-empirical surveys, missing metrics/code, duplicates).
Write concise rules matching the language of the input topic.
"""
    return await llm_router.generate_structured(
        prompt=prompt,
        schema=CriteriaGenerationResult,
        system_prompt="You are Agent 2 (PRISMA Criteria Generator). Return valid JSON strictly matching the schema.",
        temperature=0.0,
    )


async def run_pico_query_generator(
    idea: str,
    research_field: str = "",
    inclusion_criteria: list[str] | None = None,
    exclusion_criteria: list[str] | None = None,
) -> PICOQueryResult:
    """Extract English PICO components, academic keywords, and Boolean search query."""
    inc_text = "; ".join(inclusion_criteria or []) or "Not specified"
    exc_text = "; ".join(exclusion_criteria or []) or "Not specified"
    prompt = f"""
Extract the PICO framework and construct a scholarly search query (ALL values strictly in ENGLISH for OpenAlex/Scopus):
- Research Topic: "{idea.strip()}"
- Domain: "{research_field.strip() or 'Interdisciplinary Science'}"
- Inclusion Criteria: {inc_text}
- Exclusion Criteria: {exc_text}

Requirements:
1. Fill population, intervention, comparison, and outcome in concise academic English.
2. Provide 5-8 precise English academic search phrases in "search_keywords" (1-4 words each).
3. Build "boolean_query" using AND, OR, parentheses, and double quotes for multi-word phrases.
"""
    res = await llm_router.generate_structured(
        prompt=prompt,
        schema=PICOQueryResult,
        system_prompt="You are Agent 3 (PICO & Boolean Query Strategist). Return English-only JSON matching the schema.",
        temperature=0.0,
    )
    if not res.boolean_query.strip():
        res.boolean_query = build_boolean_query(res.population, res.intervention, res.search_keywords)
    return res
