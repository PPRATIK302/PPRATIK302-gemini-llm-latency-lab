"""Run a small timestamped benchmark and save CSV/JSON results."""

from __future__ import annotations

import asyncio

from latency_lab.config import load_settings
from latency_lab.demos.measure_latency import run
from latency_lab.metrics import format_summary_table, save_records, summarize_records


async def main() -> None:
    settings = load_settings()
    records = await run(repetitions=5)
    csv_path, json_path = save_records(records, settings.results_dir, "measure-latency")
    print(format_summary_table(summarize_records(records)))
    print(f"Saved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())

