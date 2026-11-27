"""pgvector Hybrid RAG Retriever & Grounded Workspace Chat Service.

Combines:
1. Strict multi-tenant & paper_ids isolation (no cross-project fallback),
2. Hybrid Reciprocal Rank Fusion (RRF) over dense cosine similarity & lexical overlap,
3. Centralized llm_router generation with mandatory [idx] citation formatting,
4. Deterministic RAG Guardrail validation.
"""

import math
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import PaperChunk
from app.models.paper import Paper
from app.services.grounding_verifier import overlap_score, tokenize
from app.services.llm_router import llm_router
from app.services.rag_guardrail import RAGGuardrailResult, rag_guardrail_service


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def rank_chunks_hybrid_rrf(
    query: str,
    query_embedding: list[float] | None,
    candidates: list[dict[str, Any]],
    *,
    top_k: int = 6,
    rrf_k: int = 60,
) -> list[dict[str, Any]]:
    """
    Fuse lexical overlap ranking and vector cosine similarity ranking via RRF.
    Each candidate dict has keys: chunk_id, paper_id, paper_title, page_number,
    section_title, content, embedding.
    """
    if not candidates:
        return []

    q_tokens = tokenize(query)

    # 1. Lexical ranking
    lex_scored = []
    for idx, c in enumerate(candidates):
        score = overlap_score(q_tokens, tokenize(c["content"]))
        lex_scored.append((idx, score))
    lex_scored.sort(key=lambda x: x[1], reverse=True)
    lex_rank = {idx: rank + 1 for rank, (idx, _) in enumerate(lex_scored)}

    # 2. Vector ranking (when embeddings exist)
    vec_rank: dict[int, int] = {}
    if query_embedding is not None:
        vec_scored = []
        for idx, c in enumerate(candidates):
            emb = c.get("embedding")
            vscore = _cosine_sim(query_embedding, emb) if emb else -1.0
            vec_scored.append((idx, vscore))
        vec_scored.sort(key=lambda x: x[1], reverse=True)
        vec_rank = {idx: rank + 1 for rank, (idx, _) in enumerate(vec_scored)}

    # 3. Reciprocal Rank Fusion
    fused = []
    for idx, c in enumerate(candidates):
        rrf_score = 1.0 / (rrf_k + lex_rank[idx])
        if idx in vec_rank:
            rrf_score += 1.0 / (rrf_k + vec_rank[idx])
        fused.append((rrf_score, {**c, "retrieval_score": round(rrf_score, 5)}))

    fused.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in fused[:top_k]]


async def retrieve_project_chunks(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    query: str,
    paper_ids: list[uuid.UUID] | None = None,
    top_k: int = 6,
) -> list[dict[str, Any]]:
    """
    Strictly retrieve chunks belonging to `project_id` (and optionally `paper_ids`).
    Falls back to Paper title+abstract segments when no PDF chunks exist for targeted papers.
    """
    stmt = (
        select(PaperChunk, Paper)
        .join(Paper, PaperChunk.paper_id == Paper.id)
        .where(Paper.project_id == project_id)
    )
    if paper_ids:
        stmt = stmt.where(Paper.id.in_(paper_ids))

    res = await db.execute(stmt)
    rows = res.all()

    candidates: list[dict[str, Any]] = [
        {
            "chunk_id": str(chunk.id),
            "paper_id": str(paper.id),
            "paper_title": paper.title,
            "page_number": chunk.page_number or 1,
            "section_title": chunk.section_title or "Full-Text",
            "content": chunk.content,
            "embedding": list(chunk.embedding) if chunk.embedding is not None else None,
        }
        for chunk, paper in rows
    ]

    # If no PDF chunks yet for the scoped project/papers, fall back cleanly to their Abstracts
    if not candidates:
        p_stmt = select(Paper).where(Paper.project_id == project_id)
        if paper_ids:
            p_stmt = p_stmt.where(Paper.id.in_(paper_ids))
        p_res = await db.execute(p_stmt)
        for paper in p_res.scalars().all():
            if paper.abstract or paper.title:
                candidates.append(
                    {
                        "chunk_id": f"abstract-{paper.id}",
                        "paper_id": str(paper.id),
                        "paper_title": paper.title,
                        "page_number": 1,
                        "section_title": "Abstract",
                        "content": f"{paper.title}. {paper.abstract or ''}".strip(),
                        "embedding": None,
                    }
                )

    if not candidates:
        return []

    has_any_embeddings = any(c["embedding"] is not None for c in candidates)
    query_emb: list[float] | None = None
    if has_any_embeddings:
        emb_list = await llm_router.embed_texts([query])
        if emb_list:
            query_emb = emb_list[0]

    return rank_chunks_hybrid_rrf(query, query_emb, candidates, top_k=top_k)


async def answer_workspace_question(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    question: str,
    paper_ids: list[uuid.UUID] | None = None,
) -> tuple[str, list[dict[str, Any]], RAGGuardrailResult]:
    """End-to-end guarded Hybrid RAG Q&A scoped to a single project."""
    ok, err = rag_guardrail_service.validate_input_query(question)
    if not ok:
        raise ValueError(err or "Invalid query")

    retrieved = await retrieve_project_chunks(
        db, project_id=project_id, query=question, paper_ids=paper_ids, top_k=6
    )

    if not retrieved:
        refusal = "Không tìm thấy thông tin phù hợp trong các bài báo đã chọn của dự án."
        guardrail = rag_guardrail_service.verify_answer_groundedness(refusal, [])
        return refusal, [], guardrail

    numbered_context = []
    citations_meta: list[dict[str, Any]] = []
    valid_keys: set[str] = set()

    for idx, ch in enumerate(retrieved, start=1):
        key = str(idx)
        valid_keys.add(key)
        numbered_context.append(
            f"[{key}] Paper: {ch['paper_title']} | Page {ch['page_number']} ({ch['section_title']})\n"
            f"Excerpt: {ch['content'][:1600]}"
        )
        citations_meta.append(
            {
                "index": idx,
                "paper_id": ch["paper_id"],
                "paper_title": ch["paper_title"],
                "page_number": ch["page_number"],
                "section_title": ch["section_title"],
                "excerpt": ch["content"][:320],
                "retrieval_score": ch.get("retrieval_score", 0.0),
            }
        )

    context_block = "\n\n".join(numbered_context)
    prompt = f"""
Answer the researcher's question using ONLY the retrieved scientific excerpts below.
Cite every factual claim inline using the exact bracket numbers e.g. [1], [2].
If the excerpts do not contain enough evidence, reply verbatim: "Không tìm thấy thông tin phù hợp trong các bài báo đã chọn."
Match the language of the user's question.

[Context Excerpts]:
{context_block}

[User Question]:
{question}
"""
    raw_answer = await llm_router.generate_text(
        prompt=prompt,
        system_prompt="You are LitNexus RAG Scholar. Never fabricate data or cite numbers outside provided context.",
        temperature=0.1,
    )

    clean_answer, _hallucinated = rag_guardrail_service.sanitize_citations(raw_answer, valid_keys)
    guardrail = rag_guardrail_service.verify_answer_groundedness(clean_answer, citations_meta)
    return clean_answer, citations_meta, guardrail
