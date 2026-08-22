"""Demo 2: choose the smallest model that passes a quality gate."""

from __future__ import annotations

import asyncio

from latency_lab.config import ROOT, load_settings
from latency_lab.evaluation import (
    choose_fastest_passing,
    load_jsonl,
    model_decision,
    serialize_decision_table,
)
from latency_lab.gemini_client import build_client
from latency_lab.metrics import new_request_id, perf_ms, utc_now
from latency_lab.schemas import ClassificationResult, LatencyRecord


CLASSIFY_PROMPT = (
    "Classify this support request as billing, technical, account, or general. "
    "Return JSON with category and confidence.\n\nRequest: {text}"
)


async def run() -> str:
    settings = load_settings()
    client = build_client(settings)
    examples = load_jsonl(ROOT / "data" / "classification_eval.jsonl")
    decisions = []
    for model in [settings.fast_model, settings.quality_model]:
        predictions: list[ClassificationResult] = []
        records: list[LatencyRecord] = []
        for example in examples:
            started_at = utc_now()
            started_ms = perf_ms()
            try:
                prediction, generation = await client.generate_structured(
                    CLASSIFY_PROMPT.format(text=example.text),
                    model=model,
                    schema=ClassificationResult,
                    timeout=settings.timeout_seconds,
                )
                predictions.append(prediction)
                records.append(
                    LatencyRecord(
                        request_id=new_request_id(),
                        experiment="compare_models",
                        model=model,
                        started_at=started_at,
                        ttft_ms=None,
                        total_latency_ms=perf_ms() - started_ms,
                        input_tokens=generation.input_tokens,
                        output_tokens=generation.output_tokens,
                        success=True,
                        error_type=None,
                        quality_score=1.0 if prediction.category == example.label else 0.0,
                    )
                )
            except Exception as exc:
                records.append(
                    LatencyRecord(
                        request_id=new_request_id(),
                        experiment="compare_models",
                        model=model,
                        started_at=started_at,
                        ttft_ms=None,
                        total_latency_ms=perf_ms() - started_ms,
                        input_tokens=None,
                        output_tokens=None,
                        success=False,
                        error_type=type(exc).__name__,
                        quality_score=0.0,
                    )
                )
        decisions.append(
            model_decision(
                model,
                predictions,
                [example.label for example in examples],
                records,
                settings.quality_threshold,
            )
        )
    table = serialize_decision_table(decisions)
    selected = choose_fastest_passing(decisions)
    if selected:
        table += f"\nQuality threshold: {settings.quality_threshold:.0%}"
    return table


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

