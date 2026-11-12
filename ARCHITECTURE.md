# LitNexus — System Architecture

## 1. The Research Funnel Model

```
[OpenAlex / Semantic Scholar: 1,000 - 3,000 Papers]
                        │
                        ▼
 ┌────────────────────────────────────────────────────────┐
 │ STAGE 1: Active Learning Hybrid Screener               │
 │  • Seed labeling: 15-20 papers (Human / LLM)           │
 │  • Local ML model (TF-IDF + LogisticRegression)        │
 │  • Uncertainty Sampling: send only borderline papers   │
 │    (0.4 <= P <= 0.6) to LLM for adjudication           │
 └────────────────────────────────────────────────────────┘
                        │  (Top 20 - 50 high-signal papers)
                        ▼
 ┌────────────────────────────────────────────────────────┐
 │ STAGE 2: Cross-Paper Conflict & Gap Discovery Engine   │
 │  1. Claim Extractor: (Method, Dataset, Metric, Claim)  │
 │  2. Cross-Examiner: Pairwise Consensus vs Conflict     │
 │  3. Gap Synthesizer: Actionable Research Gaps          │
 └────────────────────────────────────────────────────────┘
                        │
                        ▼
       [Conflict Graph + Research Gap Matrix + PRISMA]
```

## 2. Core Architectural Principles

1. **Single LLM Gateway (`app/services/llm_router.py`)**: All LLM calls go through LiteLLM with structured JSON output enforcement, retries, and provider fallback. No scattered API clients.
2. **Unified Storage (`PostgreSQL + pgvector`)**: Relational metadata (users, projects, papers, claims, conflict edges) and vector chunks live in the same transactional database.
3. **Strict Multi-Tenant Isolation**: Every project-scoped query verifies ownership at the API dependency layer (`app/api/deps.py`).
4. **Zero-Cost Academic Search First**: Built around OpenAlex polite pool and Semantic Scholar before paid search scrapers.
