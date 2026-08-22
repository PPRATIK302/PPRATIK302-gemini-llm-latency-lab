"""FastAPI application for the latency lab."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from .config import Settings, load_settings
from .gemini_client import GeminiClientError, LLMClient, build_client
from .metrics import format_summary_table, new_request_id, perf_ms, summarize_records, utc_now
from .schemas import (
    BenchmarkRequest,
    BenchmarkResponse,
    ClassificationResult,
    ClassifyRequest,
    GenerateRequest,
    GenerateResponse,
    LatencyRecord,
    RouteResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="Gemini LLM Latency Lab",
    description="Educational API for measuring and reducing LLM latency.",
    version="0.1.0",
)


def get_settings() -> Settings:
    return load_settings()


def get_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    return build_client(settings)


@app.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Health check that never calls Gemini."""

    return {"status": "ok", "mock_mode": settings.use_mock_gemini}


@app.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings),
    client: LLMClient = Depends(get_client),
) -> GenerateResponse:
    request_id = new_request_id()
    model = request.model or settings.fast_model
    started_at = utc_now()
    started_ms = perf_ms()
    try:
        result = await client.generate(
            request.prompt,
            model=model,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            timeout=settings.timeout_seconds,
        )
        total_ms = perf_ms() - started_ms
        record = LatencyRecord(
            request_id=request_id,
            experiment="generate",
            model=model,
            started_at=started_at,
            ttft_ms=None,
            total_latency_ms=total_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            success=True,
            error_type=None,
            quality_score=None,
        )
        LOGGER.info("generate_complete request_id=%s model=%s total_ms=%.1f", request_id, model, total_ms)
        return GenerateResponse(request_id=request_id, model=model, text=result.text, record=record)
    except GeminiClientError as exc:
        raise _safe_http_error(exc) from exc


@app.post("/generate/stream")
async def generate_stream(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings),
    client: LLMClient = Depends(get_client),
) -> StreamingResponse:
    request_id = new_request_id()
    model = request.model or settings.fast_model

    async def chunks() -> AsyncIterator[str]:
        started_ms = perf_ms()
        first_ms: float | None = None
        try:
            async for chunk in client.stream(
                request.prompt,
                model=model,
                temperature=request.temperature,
                max_output_tokens=request.max_output_tokens,
                timeout=settings.timeout_seconds,
            ):
                if first_ms is None:
                    first_ms = perf_ms() - started_ms
                    LOGGER.info("stream_first_token request_id=%s ttft_ms=%.1f", request_id, first_ms)
                yield chunk
            LOGGER.info("stream_complete request_id=%s total_ms=%.1f", request_id, perf_ms() - started_ms)
        except Exception:
            LOGGER.exception("stream_failed request_id=%s", request_id)
            yield "\n[stream ended with an upstream error]\n"

    return StreamingResponse(chunks(), media_type="text/plain")


@app.post("/benchmark", response_model=BenchmarkResponse)
async def benchmark(
    request: BenchmarkRequest,
    settings: Settings = Depends(get_settings),
    client: LLMClient = Depends(get_client),
) -> BenchmarkResponse:
    request_id = new_request_id()
    model = request.model or settings.fast_model
    records: list[LatencyRecord] = []
    for _ in range(request.repetitions):
        started_at = utc_now()
        started_ms = perf_ms()
        ttft_ms: float | None = None
        try:
            if request.stream:
                async for _chunk in client.stream(request.prompt, model=model, timeout=settings.timeout_seconds):
                    if ttft_ms is None:
                        ttft_ms = perf_ms() - started_ms
                input_tokens = output_tokens = None
            else:
                result = await client.generate(request.prompt, model=model, timeout=settings.timeout_seconds)
                input_tokens = result.input_tokens
                output_tokens = result.output_tokens
            records.append(
                LatencyRecord(
                    request_id=new_request_id(),
                    experiment=request.experiment,
                    model=model,
                    started_at=started_at,
                    ttft_ms=ttft_ms,
                    total_latency_ms=perf_ms() - started_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    success=True,
                    error_type=None,
                    quality_score=None,
                )
            )
        except GeminiClientError as exc:
            records.append(
                LatencyRecord(
                    request_id=new_request_id(),
                    experiment=request.experiment,
                    model=model,
                    started_at=started_at,
                    ttft_ms=ttft_ms,
                    total_latency_ms=perf_ms() - started_ms,
                    input_tokens=None,
                    output_tokens=None,
                    success=False,
                    error_type=type(exc).__name__,
                    quality_score=None,
                )
            )
    summary = summarize_records(records)
    LOGGER.info("benchmark_complete request_id=%s\n%s", request_id, format_summary_table(summary))
    return BenchmarkResponse(request_id=request_id, summary=summary, records=records)


@app.post("/classify", response_model=ClassificationResult)
async def classify(
    request: ClassifyRequest,
    settings: Settings = Depends(get_settings),
    client: LLMClient = Depends(get_client),
) -> ClassificationResult:
    model = request.model or settings.fast_model
    prompt = (
        "Classify the support request as billing, technical, account, or general. "
        "Return JSON with category and confidence.\n\nRequest:\n"
        f"{request.text}"
    )
    try:
        result, _generation = await client.generate_structured(
            prompt, model=model, schema=ClassificationResult, timeout=settings.timeout_seconds
        )
        return result
    except GeminiClientError as exc:
        raise _safe_http_error(exc) from exc


@app.post("/route", response_model=RouteResponse)
async def route(
    request: ClassifyRequest,
    settings: Settings = Depends(get_settings),
    client: LLMClient = Depends(get_client),
) -> RouteResponse:
    request_id = new_request_id()
    first = await classify(request, settings, client)
    if first.confidence >= 0.75:
        return RouteResponse(request_id=request_id, result=first, model_used=settings.fast_model, escalated=False)
    prompt = f"Carefully classify this ambiguous support request. Return JSON.\n\n{request.text}"
    result, _generation = await client.generate_structured(
        prompt, model=settings.quality_model, schema=ClassificationResult, timeout=settings.timeout_seconds
    )
    return RouteResponse(request_id=request_id, result=result, model_used=settings.quality_model, escalated=True)


@app.get("/experiments")
async def experiments() -> dict[str, list[str]]:
    return {
        "experiments": [
            "measure_latency",
            "compare_models",
            "limit_output",
            "reduce_context",
            "combine_calls",
            "parallel_tasks",
            "stream_response",
            "deterministic_vs_llm",
        ]
    }


def _safe_http_error(exc: GeminiClientError) -> HTTPException:
    LOGGER.warning("gemini_error type=%s", type(exc).__name__)
    return HTTPException(status_code=502, detail=f"Gemini request failed: {type(exc).__name__}")

