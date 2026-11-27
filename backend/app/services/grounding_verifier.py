"""Deterministic Grounding Verifier (Zero-Hallucination Anti-Fabrication Policy).

LLMs propose evidence quotes; deterministic Python token + bigram overlap verifies
whether those quotes actually exist in the paper's full-text chunks or abstract.
"""

import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS = frozenset(
    """a an the of in on at to for from with without by and or not is are was were be been
    this that these those we our their its it as than then such using used use study studies
    result results show shows showed between among during""".split()
)


@dataclass(frozen=True)
class GroundedQuoteMatch:
    quote: str
    score: float
    matched_segment: str
    page_number: int | None = None


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def overlap_score(claim_tokens: list[str], window_tokens: list[str]) -> float:
    """Compute token coverage (70%) + bigram coverage (30%) inside [0, 1]."""
    if not claim_tokens:
        return 0.0
    window_set = set(window_tokens)
    coverage = sum(1 for t in claim_tokens if t in window_set) / len(claim_tokens)

    claim_bigrams = set(zip(claim_tokens, claim_tokens[1:]))
    if claim_bigrams:
        window_bigrams = set(zip(window_tokens, window_tokens[1:]))
        bigram_coverage = len(claim_bigrams & window_bigrams) / len(claim_bigrams)
    else:
        bigram_coverage = coverage

    return round(0.7 * coverage + 0.3 * bigram_coverage, 4)


def locate_quote_in_segments(
    quote: str,
    segments: list[tuple[str, int | None]],
    *,
    min_score: float = 0.55,
) -> GroundedQuoteMatch | None:
    """Verify if `quote` is grounded in any `(text, page_number)` segment."""
    q_clean = " ".join(quote.split()).strip()
    if not q_clean:
        return None

    # 1. Exact case-insensitive substring fast path
    q_lower = q_clean.lower()
    for seg_text, page_num in segments:
        seg_norm = " ".join(seg_text.split())
        if q_lower in seg_norm.lower():
            return GroundedQuoteMatch(
                quote=quote,
                score=1.0,
                matched_segment=seg_norm[:300],
                page_number=page_num,
            )

    # 2. Deterministic token + bigram overlap fallback
    q_tokens = tokenize(q_clean)
    if not q_tokens:
        return None

    best: GroundedQuoteMatch | None = None
    for seg_text, page_num in segments:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", seg_text) if s.strip()]
        windows = sentences if sentences else [seg_text]
        # Evaluate single sentences and adjacent pairs
        candidate_windows = list(windows)
        for idx in range(len(windows) - 1):
            candidate_windows.append(f"{windows[idx]} {windows[idx + 1]}")

        for win in candidate_windows:
            score = overlap_score(q_tokens, tokenize(win))
            if score >= min_score and (best is None or score > best.score):
                best = GroundedQuoteMatch(
                    quote=quote,
                    score=score,
                    matched_segment=win[:300],
                    page_number=page_num,
                )
    return best


def verify_quotes(
    quotes: list[str],
    segments: list[tuple[str, int | None]],
    *,
    min_score: float = 0.55,
) -> tuple[list[GroundedQuoteMatch], float]:
    """
    Verify a list of quotes against paper segments.
    Returns (verified_matches, grounding_precision in [0, 1]).
    """
    clean_quotes = [q.strip() for q in quotes if q and q.strip()]
    if not clean_quotes:
        return [], 0.0

    verified: list[GroundedQuoteMatch] = []
    for q in clean_quotes:
        match = locate_quote_in_segments(q, segments, min_score=min_score)
        if match is not None:
            verified.append(match)

    precision = round(len(verified) / len(clean_quotes), 4)
    return verified, precision
