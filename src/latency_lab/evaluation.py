"""Quality evaluation and model-selection helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel

from .metrics import percentile
from .schemas import Category, ClassificationResult, LatencyRecord


class LabelledExample(BaseModel):
    text: str
    label: Category
    ambiguous: bool = False


class ModelDecision(BaseModel):
    model: str
    accuracy: float
    p50_latency_ms: float | None
    p95_latency_ms: float | None
    avg_input_tokens: float | None
    avg_output_tokens: float | None
    failed_requests: int
    passes_quality: bool


def load_jsonl(path: Path) -> list[LabelledExample]:
    """Load labelled classification examples from JSONL."""

    examples: list[LabelledExample] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                examples.append(LabelledExample.model_validate_json(line))
    return examples


def accuracy(predictions: Iterable[ClassificationResult], labels: Iterable[Category]) -> float:
    """Return exact-match classification accuracy."""

    pairs = list(zip(predictions, labels, strict=False))
    if not pairs:
        return 0.0
    correct = sum(1 for prediction, label in pairs if prediction.category == label)
    return correct / len(pairs)


def model_decision(
    model: str,
    predictions: list[ClassificationResult],
    labels: list[Category],
    records: list[LatencyRecord],
    threshold: float,
) -> ModelDecision:
    """Summarize whether a model passes the quality threshold."""

    successful = [record for record in records if record.success]
    acc = accuracy(predictions, labels)
    return ModelDecision(
        model=model,
        accuracy=acc,
        p50_latency_ms=percentile([record.total_latency_ms for record in successful], 50),
        p95_latency_ms=percentile([record.total_latency_ms for record in successful], 95),
        avg_input_tokens=_avg(record.input_tokens for record in successful),
        avg_output_tokens=_avg(record.output_tokens for record in successful),
        failed_requests=len(records) - len(successful),
        passes_quality=acc >= threshold,
    )


def choose_fastest_passing(decisions: list[ModelDecision]) -> ModelDecision | None:
    """Choose the lowest-P50 model that passes the configured quality gate."""

    passing = [decision for decision in decisions if decision.passes_quality]
    if not passing:
        return None
    return min(passing, key=lambda item: item.p50_latency_ms if item.p50_latency_ms is not None else 1e18)


def serialize_decision_table(decisions: list[ModelDecision]) -> str:
    """Render model-selection output for terminals."""

    lines = ["Model                 Accuracy   P50     P95     Passes quality"]
    for decision in decisions:
        lines.append(
            f"{decision.model:<21} {decision.accuracy:>7.1%}   "
            f"{_ms(decision.p50_latency_ms):<7} {_ms(decision.p95_latency_ms):<7} "
            f"{'Yes' if decision.passes_quality else 'No'}"
        )
    selected = choose_fastest_passing(decisions)
    if selected:
        lines.extend(
            [
                "",
                f"Recommended model: {selected.model}",
                "Reason: It is the lowest-latency model that passes the quality target.",
            ]
        )
    else:
        lines.extend(["", "Recommended model: none", "Reason: No model passed the quality target."])
    return "\n".join(lines)


def write_json(path: Path, payload: object) -> None:
    """Write JSON with stable formatting."""

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _avg(values: Iterable[int | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def _ms(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.0f}"

