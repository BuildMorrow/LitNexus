# AGENTS.md — LitNexus Engineering & Architecture Guide

You are working on **LitNexus**, an original, clean-room **Active-Learning Systematic Literature Review (SLR) & Cross-Paper Conflict Discovery Engine**.

Before planning or writing any code, read the project documentation in order:
1. `README.md` — Project overview and local setup.
2. `ARCHITECTURE.md` — High-level "Research Funnel" architecture.
3. `docs/01-architecture-overview.md` — Layered architecture, database ERD, and end-to-end sequence diagram.
4. `docs/02-features-and-modules.md` — Deep dive into Active Learning math, the 3-Agent Conflict Engine, and module mapping.
5. `docs/03-api-and-roadmap.md` — Current `/api/v1` endpoints and the Sprint 1–4 development roadmap.

---

## Core Product Architecture ("The Research Funnel")

1. **Stage 1 — Active Learning Hybrid Screener** (`backend/app/services/active_screener.py`):
   - Ingests papers from free scholarly APIs (`academic_search.py` via OpenAlex).
   - Uses local ML (`TfidfVectorizer` + `LogisticRegression` with `class_weight="balanced"`) to compute inclusion probabilities and normalized margin uncertainty $U(p) = 1 - 2|p - 0.5|$.
   - Auto-routes high-confidence papers (`auto_include` / `auto_exclude`) and restricts expensive LLM calls to borderline `uncertain` papers.

2. **Stage 2 — Cross-Paper Multi-Agent Conflict Discovery** (`backend/app/services/conflict_engine.py`):
   - **Agent 1 (Claim Extractor)**: Extracts structured `PaperClaim` records (`claim_text`, `methodology`, `dataset`, `metric_summary`, `assumptions`, `evidence_quote`).
   - **Agent 2 (Cross-Examiner)**: Compares claims across papers and creates `ConflictEdge` records (`contradicts`, `supports`, `refines`, `assumption_mismatch`) with a `debate_summary` and `root_cause_hypothesis`.
   - **Agent 3 (Research Gap Synthesizer)**: Synthesizes conflicts into actionable `ResearchGap` proposals with `novelty_score`.

---

## Non-Negotiable Engineering Rules

1. **Single LLM Gateway (`backend/app/services/llm_router.py`)**:
   - ALL LLM calls MUST go through `llm_router.generate_structured(...)` or `llm_router.generate_text(...)`.
   - NEVER import `openai`, `google-genai`, or `groq` SDKs directly inside API routes or domain services.
   - Always use Pydantic schemas for structured LLM outputs.

2. **Unified Database (`PostgreSQL 16 + pgvector`)**:
   - Use Async SQLAlchemy 2.0 (`backend/app/core/database.py`).
   - All relational data and vector chunks (`PaperChunk`) live in PostgreSQL. Do NOT introduce SQLite or external file-based vector stores (like ChromaDB) for production/application state.

3. **Strict Multi-Tenant Isolation**:
   - Every project-scoped route MUST depend on `get_owned_project` (`backend/app/api/deps.py`) or explicitly filter by `owner_id == current_user.id`.
   - Never fall back to unscoped queries across projects or users.

4. **Frontend API Boundary (`frontend/src/services/api.js`)**:
   - All HTTP requests from React MUST use `apiRequest()` and read `import.meta.env.VITE_API_URL`. Never hardcode backend hosts or IPs.

5. **Security & Git Hygiene**:
   - Never commit `.env`, API keys, or real JWT secrets. Keep `.env.example` synchronized when adding new environment variables.

6. **Verification Before Completing Tasks**:
   - Backend changes: run `pytest` and `ruff check app tests` inside `backend/`.
   - Frontend changes: run `npm run build` inside `frontend/`.
