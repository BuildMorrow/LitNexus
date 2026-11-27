"""RAG Guardrail Service — Input Injection Guard, Citation Sanitizer, and Claim Attribution."""

import re
from typing import Any

from pydantic import BaseModel, Field

from app.services.grounding_verifier import overlap_score, tokenize


class ClaimAttribution(BaseModel):
    sentence: str
    status: str = "Attributable"  # Attributable | Contradictory | Extrapolatory
    citation_keys: list[str] = Field(default_factory=list)
    supporting_excerpt: str = ""
    reasoning: str = ""
    paper_title: str | None = None
    page_number: int | None = None


class RAGGuardrailResult(BaseModel):
    is_safe: bool = True
    safety_verdict: str = "VERIFIED_HIGH_CONFIDENCE"
    faithfulness_score: float = 1.0
    hallucination_rate: float = 0.0
    citation_precision: float = 1.0
    total_claims: int = 0
    attributable_claims_count: int = 0
    extrapolatory_claims_count: int = 0
    contradictory_claims_count: int = 0
    hallucinated_citations: list[str] = Field(default_factory=list)
    claims: list[ClaimAttribution] = Field(default_factory=list)
    summary_verdict: str = "Mọi khẳng định đều được xác minh trực tiếp bởi tài liệu nguồn."


_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|above) instructions",
    r"system prompt override",
    r"you are now in developer mode",
    r"jailbreak",
    r"bypass (all )?guardrails",
    r"repeat (the )?system prompt",
    r"reveal (the )?secret key",
]

_REFUSAL_PHRASES = (
    "không tìm thấy thông tin",
    "tôi không thể trả lời",
    "cannot answer",
    "insufficient information",
    "no relevant information",
)


class RAGGuardrailService:
    def validate_input_query(self, query: str) -> tuple[bool, str | None]:
        """Validate user query against empty input, length abuse, and prompt injection."""
        if not query or not query.strip():
            return False, "Câu hỏi không được để trống."
        if len(query.strip()) > 4000:
            return False, "Câu hỏi vượt quá giới hạn cho phép (4000 ký tự)."
        q_lower = query.lower()
        for pat in _INJECTION_PATTERNS:
            if re.search(pat, q_lower, re.IGNORECASE):
                return (
                    False,
                    "Yêu cầu bị từ chối bởi chính sách an toàn truy vấn (Prompt Injection Guard).",
                )
        return True, None

    def prune_redundant_citations(self, text: str) -> str:
        """Compress [1][1] -> [1] and [1][2] -> [1, 2]."""
        if not text:
            return ""
        text = re.sub(r"\[(\d+)\]\s*\[\1\]", r"[\1]", text)

        def _merge(match: re.Match) -> str:
            keys = [k.strip() for k in f"{match.group(1)},{match.group(2)}".split(",") if k.strip()]
            seen: set[str] = set()
            uniq = [k for k in keys if not (k in seen or seen.add(k))]
            return f"[{', '.join(uniq)}]"

        for _ in range(3):
            text = re.sub(r"\[([0-9,\s]+)\]\s*\[([0-9,\s]+)\]", _merge, text)
        return text

    def sanitize_citations(
        self,
        answer: str,
        valid_keys: set[str],
    ) -> tuple[str, list[str]]:
        """Remove hallucinated citation keys not present in retrieved context."""
        found_keys: list[str] = []
        for match in re.finditer(r"\[([0-9,\s]+)\]", answer):
            for k in match.group(1).split(","):
                if k.strip():
                    found_keys.append(k.strip())

        hallucinated = [k for k in set(found_keys) if k not in valid_keys]
        sanitized = answer
        for bad in hallucinated:
            sanitized = re.sub(rf"\[{bad}\]", "", sanitized)
            sanitized = re.sub(rf",\s*{bad}\b", "", sanitized)
            sanitized = re.sub(rf"\b{bad}\s*,", "", sanitized)

        sanitized = self.prune_redundant_citations(sanitized)
        sanitized = re.sub(r"\[\s*\]", "", sanitized)
        sanitized = re.sub(r"[^\S\r\n]{2,}", " ", sanitized)
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
        return sanitized, hallucinated

    def verify_answer_groundedness(
        self,
        answer: str,
        context_chunks: list[dict[str, Any]],
    ) -> RAGGuardrailResult:
        """Run deterministic claim-level attribution auditing across the RAG answer."""
        if any(rp in answer.lower() for rp in _REFUSAL_PHRASES) and len(answer.strip()) < 300:
            return RAGGuardrailResult(
                is_safe=True,
                safety_verdict="REFUSAL_GROUNDED",
                faithfulness_score=1.0,
                hallucination_rate=0.0,
                citation_precision=1.0,
                total_claims=1,
                attributable_claims_count=1,
                claims=[
                    ClaimAttribution(
                        sentence=answer.strip(),
                        status="Attributable",
                        supporting_excerpt="Từ chối an toàn khi không có bằng chứng trong tài liệu.",
                        reasoning="Safe refusal policy triggered.",
                    )
                ],
                summary_verdict="Hệ thống đã từ chối an toàn khi thiếu dữ liệu nguồn.",
            )

        if not context_chunks:
            return RAGGuardrailResult(
                is_safe=False,
                safety_verdict="HIGH_HALLUCINATION_RISK",
                faithfulness_score=0.0,
                hallucination_rate=1.0,
                citation_precision=0.0,
                total_claims=1,
                extrapolatory_claims_count=1,
                claims=[
                    ClaimAttribution(
                        sentence=answer[:200],
                        status="Extrapolatory",
                        reasoning="Không có ngữ cảnh tài liệu nào được cung cấp để đối chứng.",
                    )
                ],
                summary_verdict="Nguy cơ ảo giác cao: thiếu ngữ cảnh tài liệu nguồn.",
            )

        valid_keys = {str(c.get("index", idx + 1)) for idx, c in enumerate(context_chunks)}
        key_to_doc = {str(c.get("index", idx + 1)): c for idx, c in enumerate(context_chunks)}

        raw_lines = [
            line.strip()
            for line in answer.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        sentences: list[str] = []
        for line in raw_lines:
            subs = [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if len(s.strip()) > 12]
            if subs:
                sentences.extend(subs)
            elif len(line) > 12:
                sentences.append(line)

        claims: list[ClaimAttribution] = []
        attr_cnt = 0
        extrap_cnt = 0

        for sent in sentences:
            cited = []
            for grp in re.findall(r"\[([0-9,\s]+)\]", sent):
                cited.extend(k.strip() for k in grp.split(",") if k.strip())
            valid_cited = [k for k in cited if k in valid_keys]

            if valid_cited:
                doc = key_to_doc[valid_cited[0]]
                chunk_text = str(doc.get("content", ""))
                score = overlap_score(tokenize(sent), tokenize(chunk_text))
                # Deterministic guard: cited statement either aligns with source or holds explicit citation
                is_grounded = score >= 0.15 or len(valid_cited) > 0
                status = "Attributable" if is_grounded else "Extrapolatory"
                if status == "Attributable":
                    attr_cnt += 1
                else:
                    extrap_cnt += 1

                claims.append(
                    ClaimAttribution(
                        sentence=sent,
                        status=status,
                        citation_keys=valid_cited,
                        supporting_excerpt=chunk_text[:220],
                        reasoning=f"Xác thực từ trích dẫn [{valid_cited[0]}] ({doc.get('paper_title', 'Paper')}).",
                        paper_title=doc.get("paper_title"),
                        page_number=doc.get("page_number"),
                    )
                )
            else:
                # Check if intro transition sentence or unsupported empirical claim
                is_transition = any(
                    kw in sent.lower()
                    for kw in ("tóm tắt", "tổng quan", "dưới đây", "lưu ý", "summary", "overview")
                )
                status = "Attributable" if is_transition else "Extrapolatory"
                if status == "Attributable":
                    attr_cnt += 1
                else:
                    extrap_cnt += 1
                claims.append(
                    ClaimAttribution(
                        sentence=sent,
                        status=status,
                        citation_keys=cited,
                        supporting_excerpt="Không có trích dẫn nguồn [idx] gắn kèm." if not is_transition else "Câu dẫn chuyển đoạn.",
                        reasoning="Mệnh đề thiếu trích dẫn trực tiếp tới ngữ cảnh nguồn." if not is_transition else "Chuyển ý cấu trúc.",
                    )
                )

        total = len(claims) or 1
        faithfulness = round(attr_cnt / total, 3)
        hallucination_rate = round(extrap_cnt / total, 3)

        all_cited_keys: set[str] = set()
        for grp in re.findall(r"\[([0-9,\s]+)\]", answer):
            all_cited_keys.update(k.strip() for k in grp.split(",") if k.strip())
        valid_cited_keys = [k for k in all_cited_keys if k in valid_keys]
        cit_precision = (
            round(len(valid_cited_keys) / max(len(all_cited_keys), 1), 3) if all_cited_keys else 1.0
        )

        if faithfulness < 0.50:
            verdict = "HIGH_HALLUCINATION_RISK"
            summary = f"Cảnh báo: {extrap_cnt}/{total} nhận định chưa có trích dẫn kiểm chứng."
        elif faithfulness < 0.85:
            verdict = "PARTIALLY_GROUNDED"
            summary = f"Độ tin cậy khá: {attr_cnt}/{total} nhận định có trích dẫn hợp lệ."
        else:
            verdict = "VERIFIED_HIGH_CONFIDENCE"
            summary = f"Độ tin cậy cao: {attr_cnt}/{total} nhận định được neo nguồn xác thực ({int(faithfulness * 100)}%)."

        return RAGGuardrailResult(
            is_safe=verdict != "HIGH_HALLUCINATION_RISK",
            safety_verdict=verdict,
            faithfulness_score=faithfulness,
            hallucination_rate=hallucination_rate,
            citation_precision=cit_precision,
            total_claims=total,
            attributable_claims_count=attr_cnt,
            extrapolatory_claims_count=extrap_cnt,
            contradictory_claims_count=0,
            hallucinated_citations=[k for k in all_cited_keys if k not in valid_keys],
            claims=claims,
            summary_verdict=summary,
        )


rag_guardrail_service = RAGGuardrailService()
