import json
import logging
import os
import re
import time
from typing import TypeVar

import litellm
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMGatewayError(RuntimeError):
    """Raised when all configured LLM providers fail."""


class LLMRouter:
    """Single centralized gateway for all LLM calls via LiteLLM."""

    def __init__(self) -> None:
        settings = get_settings()
        self.models = [settings.LLM_PRIMARY_MODEL, *settings.fallback_models_list]
        self.embedding_model = settings.LLM_EMBEDDING_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self._sync_provider_env(settings)
        self.usage_stats: dict[str, int | float | list[dict]] = {
            "total_calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "recent_calls": [],
        }

    @staticmethod
    def _sync_provider_env(settings) -> None:
        if settings.GEMINI_API_KEY:
            os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        if settings.OPENAI_API_KEY:
            os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        if settings.GROQ_API_KEY:
            os.environ.setdefault("GROQ_API_KEY", settings.GROQ_API_KEY)

    @staticmethod
    def _extract_json(raw: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        return text

    def _record_usage(self, model: str, response: object, latency_ms: int, task_kind: str) -> None:
        usage = getattr(response, "usage", None)
        p_tok = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
        c_tok = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
        t_tok = int(getattr(usage, "total_tokens", p_tok + c_tok) or (p_tok + c_tok))
        # Conservative blended Flash/Mini rate ($0.15 / 1M in, $0.60 / 1M out)
        cost = round((p_tok * 0.15 + c_tok * 0.60) / 1_000_000, 6)

        self.usage_stats["total_calls"] = int(self.usage_stats["total_calls"]) + 1
        self.usage_stats["prompt_tokens"] = int(self.usage_stats["prompt_tokens"]) + p_tok
        self.usage_stats["completion_tokens"] = int(self.usage_stats["completion_tokens"]) + c_tok
        self.usage_stats["total_tokens"] = int(self.usage_stats["total_tokens"]) + t_tok
        self.usage_stats["estimated_cost_usd"] = round(
            float(self.usage_stats["estimated_cost_usd"]) + cost, 6
        )
        recent = list(self.usage_stats["recent_calls"])
        recent.append(
            {
                "task": task_kind,
                "model": model,
                "total_tokens": t_tok,
                "latency_ms": latency_ms,
                "cost_usd": cost,
            }
        )
        self.usage_stats["recent_calls"] = recent[-20:]

    async def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str = "You are a rigorous academic research assistant. Output valid JSON only.",
        temperature: float | None = None,
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        full_system = (
            f"{system_prompt}\n\nRespond strictly with JSON matching this schema:\n{schema_json}"
        )

        last_error: Exception | None = None
        for model in self.models:
            t0 = time.perf_counter()
            try:
                response = await litellm.acompletion(
                    model=model,
                    messages=[
                        {"role": "system", "content": full_system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature if temperature is not None else self.temperature,
                    response_format={"type": "json_object"},
                )
                latency_ms = int((time.perf_counter() - t0) * 1000)
                self._record_usage(model, response, latency_ms, schema.__name__)
                content = response.choices[0].message.content or "{}"
                cleaned = self._extract_json(content)
                return schema.model_validate_json(cleaned)
            except Exception as exc:
                logger.warning("LLM model %s failed: %s", model, exc)
                last_error = exc

        raise LLMGatewayError(f"All LLM models failed: {last_error}")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful academic research assistant.",
        temperature: float | None = None,
    ) -> str:
        last_error: Exception | None = None
        for model in self.models:
            t0 = time.perf_counter()
            try:
                response = await litellm.acompletion(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature if temperature is not None else self.temperature,
                )
                latency_ms = int((time.perf_counter() - t0) * 1000)
                self._record_usage(model, response, latency_ms, "generate_text")
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                logger.warning("LLM model %s failed: %s", model, exc)
                last_error = exc

        raise LLMGatewayError(f"All LLM models failed: {last_error}")

    async def embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        """Generate dense embeddings via LiteLLM; gracefully returns None if unconfigured."""
        if not texts:
            return []
        try:
            resp = await litellm.aembedding(model=self.embedding_model, input=texts)
            return [item["embedding"] for item in resp.data]
        except Exception as exc:
            logger.warning("Embedding generation skipped/failed (%s): %s", self.embedding_model, exc)
            return None


llm_router = LLMRouter()
