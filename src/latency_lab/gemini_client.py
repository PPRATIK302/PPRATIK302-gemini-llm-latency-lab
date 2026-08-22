"""Gemini client abstraction with real and mock implementations."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from .config import Settings, load_settings
from .schemas import Category, ClassificationResult, GenerationResult, WorkflowPlan

LOGGER = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiClientError(RuntimeError):
    """Base exception for Gemini client failures."""


class GeminiAuthenticationError(GeminiClientError):
    """Raised when the API key is missing or rejected."""


class GeminiRetryableError(GeminiClientError):
    """Raised when a failure may succeed if retried."""


class GeminiValidationError(GeminiClientError):
    """Raised when the response cannot be validated."""


class LLMClient(Protocol):
    async def generate(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> GenerationResult: ...

    async def stream(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> AsyncIterator[str]: ...

    async def generate_structured(
        self,
        prompt: str,
        *,
        model: str,
        schema: type[T],
        temperature: float = 0.0,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> tuple[T, GenerationResult]: ...


def _keyword_category(text: str) -> tuple[Category, float]:
    lowered = text.lower()
    if any(word in lowered for word in ["invoice", "refund", "charge", "payment", "billing"]):
        return "billing", 0.94
    if any(word in lowered for word in ["bug", "error", "api", "timeout", "install"]):
        return "technical", 0.92
    if any(word in lowered for word in ["login", "password", "account", "profile", "sign in"]):
        return "account", 0.91
    if any(word in lowered for word in ["maybe", "unclear", "not sure", "ambiguous"]):
        return "general", 0.54
    return "general", 0.82


class MockGeminiClient:
    """Deterministic offline Gemini substitute for development, CI and docs."""

    def __init__(
        self,
        *,
        delay_ms: int = 40,
        stream_delay_ms: int = 10,
        fail_experiment: str | None = None,
    ) -> None:
        self.delay_ms = delay_ms
        self.stream_delay_ms = stream_delay_ms
        self.fail_experiment = fail_experiment

    async def _maybe_fail(self, prompt: str) -> None:
        if self.fail_experiment and self.fail_experiment in prompt:
            raise GeminiRetryableError("simulated retryable mock failure")

    async def generate(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> GenerationResult:
        del temperature, timeout
        await self._maybe_fail(prompt)
        await asyncio.sleep(self.delay_ms / 1000)
        text = self._mock_text(prompt, max_output_tokens=max_output_tokens)
        return GenerationResult(
            text=text,
            input_tokens=max(1, len(prompt.split())),
            output_tokens=max(1, len(text.split())),
            raw={"mock": True, "model": model},
        )

    async def stream(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        del model, temperature, timeout
        await self._maybe_fail(prompt)
        text = self._mock_text(prompt, max_output_tokens=max_output_tokens)
        for chunk in text.split():
            await asyncio.sleep(self.stream_delay_ms / 1000)
            yield chunk + " "

    async def generate_structured(
        self,
        prompt: str,
        *,
        model: str,
        schema: type[T],
        temperature: float = 0.0,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> tuple[T, GenerationResult]:
        del temperature, max_output_tokens, timeout
        await self._maybe_fail(prompt)
        await asyncio.sleep(self.delay_ms / 1000)
        payload: dict[str, Any]
        if schema is ClassificationResult:
            category, confidence = _keyword_category(prompt)
            payload = {"category": category, "confidence": confidence}
        elif schema is WorkflowPlan:
            category, _ = _keyword_category(prompt)
            payload = {
                "intent": category,
                "search_query": " ".join(prompt.split()[-8:]),
                "requires_retrieval": category in {"billing", "technical", "account"},
            }
        else:
            payload = {}
        text = json.dumps(payload)
        parsed = schema.model_validate(payload)
        return parsed, GenerationResult(
            text=text,
            input_tokens=max(1, len(prompt.split())),
            output_tokens=max(1, len(text.split())),
            raw={"mock": True, "model": model},
        )

    def _mock_text(self, prompt: str, *, max_output_tokens: int) -> str:
        category, confidence = _keyword_category(prompt)
        if "category and confidence" in prompt.lower() or "classify" in prompt.lower():
            return json.dumps({"category": category, "confidence": confidence})
        words = (
            "Mock Gemini response. This offline answer is deterministic and intended for latency "
            "lab development, CI, and documentation. It should never be treated as a real benchmark."
        ).split()
        return " ".join(words[:max_output_tokens])


class GeminiClient:
    """Thin wrapper around the official google-genai SDK."""

    def __init__(self, api_key: str, *, retries: int = 2, base_backoff: float = 0.25) -> None:
        if not api_key:
            raise GeminiAuthenticationError("GEMINI_API_KEY is required unless USE_MOCK_GEMINI=true")
        from google import genai

        self._client = genai.Client(api_key=api_key).aio
        self._retries = retries
        self._base_backoff = base_backoff

    async def generate(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> GenerationResult:
        from google.genai import types

        async def call() -> Any:
            return await asyncio.wait_for(
                self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                ),
                timeout=timeout,
            )

        response = await self._with_retries(call)
        return self._to_generation_result(response)

    async def stream(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        from google.genai import types

        try:
            if timeout is None:
                stream = await self._client.models.generate_content_stream(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                )
                async for chunk in stream:
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
            else:
                async with asyncio.timeout(timeout):
                    stream = await self._client.models.generate_content_stream(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                        ),
                    )
                    async for chunk in stream:
                        text = getattr(chunk, "text", None)
                        if text:
                            yield text
        except asyncio.CancelledError:
            LOGGER.info("stream cancelled by client")
            raise
        except Exception as exc:
            raise self._map_error(exc) from exc

    async def generate_structured(
        self,
        prompt: str,
        *,
        model: str,
        schema: type[T],
        temperature: float = 0.0,
        max_output_tokens: int = 256,
        timeout: float | None = None,
    ) -> tuple[T, GenerationResult]:
        from google.genai import types

        async def call() -> Any:
            return await asyncio.wait_for(
                self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                ),
                timeout=timeout,
            )

        response = await self._with_retries(call)
        result = self._to_generation_result(response)
        try:
            return schema.model_validate_json(result.text), result
        except ValidationError as exc:
            raise GeminiValidationError("Gemini response did not match the requested schema") from exc

    async def _with_retries(self, call: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                return await call()
            except Exception as exc:
                mapped = self._map_error(exc)
                if not isinstance(mapped, GeminiRetryableError) or attempt >= self._retries:
                    raise mapped from exc
                last_error = mapped
                await asyncio.sleep(self._base_backoff * (2**attempt))
        raise GeminiRetryableError("retry attempts exhausted") from last_error

    def _map_error(self, exc: Exception) -> GeminiClientError:
        message = str(exc)
        lowered = message.lower()
        if "api key" in lowered or "permission" in lowered or "unauthenticated" in lowered:
            return GeminiAuthenticationError("Gemini authentication failed")
        if isinstance(exc, TimeoutError | asyncio.TimeoutError) or any(
            word in lowered for word in ["429", "rate", "timeout", "temporarily", "503", "500"]
        ):
            return GeminiRetryableError("Gemini request failed with a retryable error")
        return GeminiClientError("Gemini request failed")

    def _to_generation_result(self, response: Any) -> GenerationResult:
        text = getattr(response, "text", None)
        if text is None:
            raise GeminiValidationError("Gemini response did not contain text")
        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None) if usage else None
        output_tokens = getattr(usage, "candidates_token_count", None) if usage else None
        return GenerationResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw=None,
        )


def build_client(settings: Settings | None = None) -> LLMClient:
    """Build a real or mock client from environment settings."""

    settings = settings or load_settings()
    if settings.use_mock_gemini:
        return MockGeminiClient(
            delay_ms=settings.mock_delay_ms,
            stream_delay_ms=settings.mock_stream_delay_ms,
            fail_experiment=settings.mock_fail_experiment,
        )
    return GeminiClient(settings.gemini_api_key or "")
