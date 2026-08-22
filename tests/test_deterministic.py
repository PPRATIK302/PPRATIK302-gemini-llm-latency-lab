import asyncio
from datetime import date
from decimal import Decimal

from latency_lab.deterministic import (
    apply_discount,
    can_access,
    concurrent_services,
    invoice_total,
    is_after,
    sequential_services,
)
from latency_lab.metrics import perf_ms


def test_business_rules_are_exact() -> None:
    assert is_after(date(2026, 8, 22), date(2026, 8, 21))
    assert invoice_total([Decimal("10.00"), Decimal("2.50")], Decimal("0.08")) == Decimal("13.50")
    assert can_access({"support"}, "support")
    assert apply_discount(Decimal("100.00"), "enterprise") == Decimal("88.00")


async def test_concurrent_services_are_faster_than_sequential() -> None:
    start = perf_ms()
    await sequential_services(20)
    sequential = perf_ms() - start
    start = perf_ms()
    await concurrent_services(20)
    concurrent = perf_ms() - start
    assert concurrent < sequential


def test_asyncio_marker_smoke() -> None:
    assert asyncio.run(concurrent_services(1))

