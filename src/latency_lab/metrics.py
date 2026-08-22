"""Latency measurement and result persistence."""

from __future__ import annotations

import csv
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .schemas import LatencyRecord


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def new_request_id() -> str:
    """Create a short request id for logs and benchmark rows."""

    return uuid4().hex[:12]


def perf_ms() -> float:
    """Return a monotonic timestamp in milliseconds."""

    return time.perf_counter() * 1000


def percentile(values: Iterable[float], percent: float) -> float | None:
    """Calculate a nearest-rank percentile with linear interpolation."""

    clean = sorted(float(value) for value in values)
    if not clean:
        return None
    if percent <= 0:
        return clean[0]
    if percent >= 100:
        return clean[-1]
    index = (len(clean) - 1) * (percent / 100)
    lower = int(index)
    upper = min(lower + 1, len(clean) - 1)
    fraction = index - lower
    return clean[lower] + (clean[upper] - clean[lower]) * fraction


def summarize_records(records: list[LatencyRecord]) -> dict[str, float | int | None]:
    """Summarize latency, token, error-rate and throughput metrics."""

    total = len(records)
    successes = [record for record in records if record.success]
    latencies = [record.total_latency_ms for record in successes]
    ttfts = [record.ttft_ms for record in successes if record.ttft_ms is not None]
    first_started = min((record.started_at for record in records), default=None)
    elapsed_ms = sum(record.total_latency_ms for record in records)
    throughput = (len(successes) / elapsed_ms * 1000) if elapsed_ms > 0 else None
    return {
        "requests": total,
        "successful": len(successes),
        "failed": total - len(successes),
        "error_rate": (total - len(successes)) / total if total else 0.0,
        "p50_total_latency_ms": percentile(latencies, 50),
        "p95_total_latency_ms": percentile(latencies, 95),
        "p50_ttft_ms": percentile(ttfts, 50),
        "p95_ttft_ms": percentile(ttfts, 95),
        "avg_input_tokens": statistics.fmean(
            record.input_tokens for record in successes if record.input_tokens is not None
        )
        if any(record.input_tokens is not None for record in successes)
        else None,
        "avg_output_tokens": statistics.fmean(
            record.output_tokens for record in successes if record.output_tokens is not None
        )
        if any(record.output_tokens is not None for record in successes)
        else None,
        "throughput_rps": throughput,
        "started_at_epoch": first_started.timestamp() if first_started else None,
    }


def format_summary_table(summary: dict[str, float | int | None]) -> str:
    """Render a small terminal table for demos."""

    def ms(value: float | int | None) -> str:
        return "unavailable" if value is None else f"{float(value):.0f} ms"

    error_rate = float(summary["error_rate"] or 0) * 100
    return "\n".join(
        [
            f"Requests:           {summary['requests']}",
            f"Successful:         {summary['successful']}",
            f"Error rate:         {error_rate:.1f}%",
            f"P50 total latency:  {ms(summary['p50_total_latency_ms'])}",
            f"P95 total latency:  {ms(summary['p95_total_latency_ms'])}",
            f"P50 TTFT:           {ms(summary['p50_ttft_ms'])}",
            f"P95 TTFT:           {ms(summary['p95_ttft_ms'])}",
        ]
    )


def save_records(records: list[LatencyRecord], results_dir: Path, prefix: str) -> tuple[Path, Path]:
    """Save benchmark records as timestamped CSV and JSON files."""

    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().strftime("%Y%m%d-%H%M%S")
    safe_prefix = "".join(char if char.isalnum() or char in "-_" else "-" for char in prefix)
    csv_path = results_dir / f"{stamp}-{safe_prefix}.csv"
    json_path = results_dir / f"{stamp}-{safe_prefix}.json"

    rows = [record.model_dump(mode="json") for record in records]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
    return csv_path, json_path

