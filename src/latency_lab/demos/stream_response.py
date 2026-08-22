"""Demo 7: streaming improves perceived responsiveness."""

from __future__ import annotations

import asyncio

from latency_lab.config import load_settings
from latency_lab.gemini_client import build_client
from latency_lab.metrics import perf_ms


async def run() -> dict[str, float | None]:
    settings = load_settings()
    client = build_client(settings)
    prompt = "Explain three ways to reduce latency in an LLM application."
    start = perf_ms()
    await client.generate(prompt, model=settings.fast_model, max_output_tokens=64)
    non_stream_ms = perf_ms() - start
    start = perf_ms()
    ttft_ms: float | None = None
    async for _chunk in client.stream(prompt, model=settings.fast_model, max_output_tokens=64):
        if ttft_ms is None:
            ttft_ms = perf_ms() - start
    stream_ms = perf_ms() - start
    return {
        "non_stream_total_ms": round(non_stream_ms, 1),
        "stream_ttft_ms": round(ttft_ms, 1) if ttft_ms is not None else None,
        "stream_total_ms": round(stream_ms, 1),
    }


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

