"""Demo 5: reduce sequential model calls."""

from __future__ import annotations

import asyncio

from latency_lab.config import load_settings
from latency_lab.gemini_client import build_client
from latency_lab.metrics import perf_ms
from latency_lab.schemas import ClassificationResult, WorkflowPlan


async def run() -> dict[str, object]:
    settings = load_settings()
    client = build_client(settings)
    text = "The invoice total is wrong and I need documents about refund timing."
    start = perf_ms()
    intent, _ = await client.generate_structured(
        f"Classify this request. Return JSON.\n{text}",
        model=settings.fast_model,
        schema=ClassificationResult,
    )
    rewrite = await client.generate(
        f"Rewrite this as a search query only.\n{text}", model=settings.fast_model, max_output_tokens=32
    )
    retrieval = await client.generate(
        f"Answer true or false: does this need retrieval?\n{text}",
        model=settings.fast_model,
        max_output_tokens=16,
    )
    sequential_ms = perf_ms() - start

    start = perf_ms()
    plan, generation = await client.generate_structured(
        "Return one JSON object with intent, search_query, and requires_retrieval.\n"
        f"Support request: {text}",
        model=settings.fast_model,
        schema=WorkflowPlan,
    )
    combined_ms = perf_ms() - start
    return {
        "sequential_calls": 3,
        "combined_calls": 1,
        "sequential_latency_ms": round(sequential_ms, 1),
        "combined_latency_ms": round(combined_ms, 1),
        "sequential_valid": bool(intent.category and rewrite.text and retrieval.text),
        "combined_valid": bool(plan.intent and plan.search_query),
        "combined_output_tokens": generation.output_tokens,
    }


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

