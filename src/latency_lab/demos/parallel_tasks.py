"""Demo 6: run independent work concurrently."""

from __future__ import annotations

import asyncio

from latency_lab.deterministic import concurrent_services, sequential_services
from latency_lab.metrics import perf_ms


async def run(delay_ms: int = 100) -> dict[str, object]:
    start = perf_ms()
    sequential = await sequential_services(delay_ms)
    sequential_ms = perf_ms() - start
    start = perf_ms()
    concurrent = await concurrent_services(delay_ms)
    concurrent_ms = perf_ms() - start
    return {
        "sequential_results": sequential,
        "concurrent_results": concurrent,
        "sequential_latency_ms": round(sequential_ms, 1),
        "concurrent_latency_ms": round(concurrent_ms, 1),
    }


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

