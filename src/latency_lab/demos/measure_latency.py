"""Demo 1: measure user-visible latency."""

from __future__ import annotations

import asyncio

from latency_lab.config import load_settings
from latency_lab.gemini_client import build_client
from latency_lab.metrics import format_summary_table, new_request_id, perf_ms, summarize_records, utc_now
from latency_lab.schemas import LatencyRecord


async def run(repetitions: int = 5, *, stream: bool = True, model_override: str | None = None) -> list[LatencyRecord]:
    settings = load_settings()
    client = build_client(settings)
    model = model_override or settings.fast_model
    prompt = "Classify this support request: I cannot sign in after resetting my password."
    records: list[LatencyRecord] = []
    for _ in range(repetitions):
        started_at = utc_now()
        started_ms = perf_ms()
        ttft_ms: float | None = None
        try:
            if stream:
                async for _chunk in client.stream(prompt, model=model, timeout=settings.timeout_seconds):
                    if ttft_ms is None:
                        ttft_ms = perf_ms() - started_ms
            else:
                result = await client.generate(prompt, model=model, timeout=settings.timeout_seconds)
                input_tokens = result.input_tokens
                output_tokens = result.output_tokens
            records.append(
                LatencyRecord(
                    request_id=new_request_id(),
                    experiment="measure_latency",
                    model=model,
                    started_at=started_at,
                    ttft_ms=ttft_ms,
                    total_latency_ms=perf_ms() - started_ms,
                    input_tokens=None if stream else input_tokens,
                    output_tokens=None if stream else output_tokens,
                    success=True,
                    error_type=None,
                    quality_score=None,
                )
            )
        except Exception as exc:
            records.append(
                LatencyRecord(
                    request_id=new_request_id(),
                    experiment="measure_latency",
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
    return records


async def main() -> None:
    records = await run()
    print("Runtime output from this machine, not guaranteed sample output")
    print(format_summary_table(summarize_records(records)))


if __name__ == "__main__":
    asyncio.run(main())
