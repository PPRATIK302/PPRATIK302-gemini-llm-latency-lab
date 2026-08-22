"""Run every demo in mock mode or real mode depending on environment."""

from __future__ import annotations

import asyncio

from latency_lab.demos import (
    combine_calls,
    compare_models,
    deterministic_vs_llm,
    limit_output,
    measure_latency,
    parallel_tasks,
    reduce_context,
    stream_response,
)
from latency_lab.metrics import format_summary_table, summarize_records


async def main() -> None:
    print("\n== Measure latency ==")
    print(format_summary_table(summarize_records(await measure_latency.run(repetitions=3))))
    print("\n== Compare models ==")
    print(await compare_models.run())
    print("\n== Limit output ==")
    print(await limit_output.run())
    print("\n== Reduce context ==")
    print(await reduce_context.run())
    print("\n== Combine calls ==")
    print(await combine_calls.run())
    print("\n== Parallel tasks ==")
    print(await parallel_tasks.run())
    print("\n== Stream response ==")
    print(await stream_response.run())
    print("\n== Deterministic vs LLM ==")
    print(await deterministic_vs_llm.run())


if __name__ == "__main__":
    asyncio.run(main())

