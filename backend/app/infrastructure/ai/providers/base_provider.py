from abc import ABC, abstractmethod

import httpx

from app.application.dto.enrichment_dto import ClinicAIInput, LLMCompletion
from app.application.ports.llm_provider import LLMProvider
from app.infrastructure.ai.enrichment_parser import (
    PROMPT_VERSION,
    REPAIR_USER_SUFFIX,
    EnrichmentParseError,
    build_user_prompt,
    parse_enrichment_response,
)


class TransientLLMError(Exception):
    pass


class BaseLLMProvider(ABC, LLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_site_text_chars: int = 8000,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_site_text_chars = max_site_text_chars
        self._timeout_seconds = timeout_seconds

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def prompt_version(self) -> str:
        return PROMPT_VERSION

    def analyze_clinic(self, payload: ClinicAIInput) -> LLMCompletion:
        system_prompt, user_prompt = build_user_prompt(payload, self._max_site_text_chars)
        raw = self._complete(system_prompt, user_prompt)
        try:
            result = parse_enrichment_response(raw)
        except EnrichmentParseError:
            repair_prompt = user_prompt + REPAIR_USER_SUFFIX.format(previous=raw)
            repair_raw = self._complete(system_prompt, repair_prompt)
            result = parse_enrichment_response(repair_raw)

        return LLMCompletion(
            provider=self.provider_name,
            model=self.model_name,
            prompt_version=self.prompt_version,
            result=result,
        )

    @abstractmethod
    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return raw model text."""

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in {408, 429, 500, 502, 503, 504}:
            raise TransientLLMError(
                f"{self.provider_name} transient error {response.status_code}: {response.text}"
            )
        response.raise_for_status()


class GPTProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "gpt"

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise TransientLLMError("OPENAI_API_KEY is not configured")

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=self._timeout_seconds,
        )
        self._raise_for_status(response)
        body = response.json()
        return body["choices"][0]["message"]["content"]


class ClaudeProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "claude"

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise TransientLLMError("ANTHROPIC_API_KEY is not configured")

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": 512,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=self._timeout_seconds,
        )
        self._raise_for_status(response)
        body = response.json()
        parts = body.get("content") or []
        texts = [part.get("text", "") for part in parts if part.get("type") == "text"]
        return "".join(texts)


class GeminiProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "gemini"

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise TransientLLMError("GEMINI_API_KEY is not configured")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"
        )
        response = httpx.post(
            url,
            headers={
                "x-goog-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=self._timeout_seconds,
        )
        self._raise_for_status(response)
        body = response.json()
        candidates = body.get("candidates") or []
        if not candidates:
            raise TransientLLMError("Gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts") or []
        texts = [part.get("text", "") for part in parts if part.get("text")]
        return "".join(texts)
