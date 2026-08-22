"""Demo 3: fewer output tokens."""

from __future__ import annotations

import asyncio

from latency_lab.config import load_settings
from latency_lab.gemini_client import build_client
from latency_lab.metrics import perf_ms
from latency_lab.schemas import ClassificationResult


async def run() -> dict[str, object]:
    settings = load_settings()
    client = build_client(settings)
    model = settings.fast_model
    verbose_prompt = (
        "Explain in detail what team should handle this request and why: "
        "I was charged twice for my April invoice."
    )
    concise_prompt = (
        "Classify this support request. Return category and confidence only: "
        "I was charged twice for my April invoice."
    )
    start = perf_ms()
    verbose = await client.generate(verbose_prompt, model=model, max_output_tokens=256)
    verbose_ms = perf_ms() - start
    start = perf_ms()
    structured, concise = await client.generate_structured(
        concise_prompt, model=model, schema=ClassificationResult, max_output_tokens=32
    )
    concise_ms = perf_ms() - start
    return {
        "unrestricted_output_tokens": verbose.output_tokens,
        "constrained_output_tokens": concise.output_tokens,
        "unrestricted_latency_ms": round(verbose_ms, 1),
        "constrained_latency_ms": round(concise_ms, 1),
        "structured_valid": True,
        "category": structured.category,
    }


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

