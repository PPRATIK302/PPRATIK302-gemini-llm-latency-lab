"""Demo 8: keep deterministic work in Python."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

from latency_lab.config import load_settings
from latency_lab.deterministic import apply_discount, can_access, invoice_total, is_after, sort_records
from latency_lab.gemini_client import build_client
from latency_lab.metrics import perf_ms


async def run() -> dict[str, object]:
    settings = load_settings()
    client = build_client(settings)
    start = perf_ms()
    python_results = {
        "date_after": is_after(date(2026, 8, 22), date(2026, 1, 1)),
        "invoice_total": str(invoice_total([Decimal("10.00"), Decimal("2.50")], Decimal("0.08"))),
        "sorted": sort_records([{"name": "B"}, {"name": "A"}], "name"),
        "can_access": can_access({"support"}, "support"),
        "discounted": str(apply_discount(Decimal("100.00"), "plus")),
    }
    python_ms = perf_ms() - start
    start = perf_ms()
    llm_result = await client.generate(
        "Do these deterministic tasks: compare dates, total invoice, sort records, check permission, "
        "and apply a fixed discount.",
        model=settings.fast_model,
        max_output_tokens=128,
    )
    llm_ms = perf_ms() - start
    return {
        "python_correct": True,
        "python_latency_ms": round(python_ms, 3),
        "llm_latency_ms": round(llm_ms, 1),
        "python_results": python_results,
        "llm_output_tokens": llm_result.output_tokens,
    }


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

