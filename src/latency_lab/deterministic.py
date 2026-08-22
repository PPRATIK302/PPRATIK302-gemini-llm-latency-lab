"""Deterministic tasks that should stay in ordinary Python code."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


def is_after(first: date, second: date) -> bool:
    """Compare dates exactly."""

    return first > second


def invoice_total(amounts: Iterable[Decimal], tax_rate: Decimal) -> Decimal:
    """Calculate invoice total using Decimal for money."""

    subtotal = sum(amounts, Decimal("0.00"))
    total = subtotal * (Decimal("1.00") + tax_rate)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def sort_records(records: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    """Sort records by a fixed key."""

    return sorted(records, key=lambda record: str(record[key]))


def can_access(user_roles: set[str], required_role: str) -> bool:
    """Evaluate a deterministic permission check."""

    return "admin" in user_roles or required_role in user_roles


def apply_discount(amount: Decimal, customer_tier: str) -> Decimal:
    """Apply fixed discount rules."""

    discounts = {"standard": Decimal("0.00"), "plus": Decimal("0.05"), "enterprise": Decimal("0.12")}
    discount = discounts.get(customer_tier, Decimal("0.00"))
    return (amount * (Decimal("1.00") - discount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def documentation_search(delay_ms: int = 100) -> dict[str, str]:
    """Simulate an independent documentation search service."""

    await asyncio.sleep(delay_ms / 1000)
    return {"source": "docs", "status": "found"}


async def account_status_lookup(delay_ms: int = 120) -> dict[str, str]:
    """Simulate an independent account-status service."""

    await asyncio.sleep(delay_ms / 1000)
    return {"source": "account", "status": "active"}


async def sequential_services(delay_ms: int = 100) -> list[object]:
    """Run independent services sequentially for comparison."""

    first = await documentation_search(delay_ms)
    second = await account_status_lookup(delay_ms)
    return [first, second]


async def concurrent_services(delay_ms: int = 100) -> list[object]:
    """Run independent services concurrently and retain partial failures."""

    return list(
        await asyncio.gather(
            documentation_search(delay_ms),
            account_status_lookup(delay_ms),
            return_exceptions=True,
        )
    )

