from datetime import UTC, datetime

from latency_lab.metrics import percentile, summarize_records
from latency_lab.schemas import LatencyRecord


def test_percentile_interpolates() -> None:
    assert percentile([100, 200, 300], 50) == 200
    assert percentile([100, 200, 300], 95) == 290
    assert percentile([], 50) is None


def test_summary_keeps_non_streaming_ttft_unavailable() -> None:
    record = LatencyRecord(
        request_id="r1",
        experiment="unit",
        model="mock",
        started_at=datetime.now(UTC),
        ttft_ms=None,
        total_latency_ms=120,
        input_tokens=10,
        output_tokens=4,
        success=True,
        error_type=None,
        quality_score=None,
    )
    summary = summarize_records([record])
    assert summary["p50_ttft_ms"] is None
    assert summary["p50_total_latency_ms"] == 120

