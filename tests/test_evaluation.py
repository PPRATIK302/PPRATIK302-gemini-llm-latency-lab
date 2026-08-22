from datetime import UTC, datetime

from latency_lab.evaluation import choose_fastest_passing, model_decision
from latency_lab.schemas import ClassificationResult, LatencyRecord


def _record(model: str, latency: float, success: bool = True) -> LatencyRecord:
    return LatencyRecord(
        request_id="r",
        experiment="unit",
        model=model,
        started_at=datetime.now(UTC),
        ttft_ms=None,
        total_latency_ms=latency,
        input_tokens=10,
        output_tokens=2,
        success=success,
        error_type=None if success else "Boom",
        quality_score=None,
    )


def test_model_selection_uses_quality_threshold() -> None:
    labels = ["billing", "technical"]
    fast = model_decision(
        "fast",
        [
            ClassificationResult(category="billing", confidence=0.9),
            ClassificationResult(category="general", confidence=0.4),
        ],
        labels,
        [_record("fast", 50), _record("fast", 70)],
        0.9,
    )
    quality = model_decision(
        "quality",
        [
            ClassificationResult(category="billing", confidence=0.9),
            ClassificationResult(category="technical", confidence=0.9),
        ],
        labels,
        [_record("quality", 100), _record("quality", 110)],
        0.9,
    )
    assert not fast.passes_quality
    assert choose_fastest_passing([fast, quality]) == quality
