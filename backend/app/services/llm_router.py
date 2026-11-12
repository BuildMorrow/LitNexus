import json
import logging
import os
import re
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
        self.temperature = settings.LLM_TEMPERATURE
        self._sync_provider_env(settings)

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

    async def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str = "You are a rigorous academic research assistant. Output valid JSON only.",
        temperature: float | None = None,
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        full_system = (
            f"{system_prompt}\n\n"
            f"Respond strictly with JSON matching this schema:\n{schema_json}"
        )

        last_error: Exception | None = None
        for model in self.models:
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
            try:
                response = await litellm.acompletion(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature if temperature is not None else self.temperature,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                logger.warning("LLM model %s failed: %s", model, exc)
                last_error = exc

        raise LLMGatewayError(f"All LLM models failed: {last_error}")


llm_router = LLMRouter()
