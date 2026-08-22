"""Evaluate configured models against the classification dataset."""

from __future__ import annotations

import asyncio

from latency_lab.demos.compare_models import run


if __name__ == "__main__":
    print(asyncio.run(run()))
