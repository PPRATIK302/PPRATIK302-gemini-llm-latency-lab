# 08. Deterministic Code

## Core idea

Keep fixed rules and exact calculations in ordinary Python code.

## Why it affects latency

Python functions are faster, cheaper, testable, and deterministic for fixed rules.

## Before implementation

Ask an LLM to compare dates, calculate invoice totals, sort records, check permissions, or apply discounts.

## Optimized implementation

Use Python functions in `latency_lab.deterministic` and `Decimal` for money.

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.deterministic_vs_llm
```

## Example terminal output, illustrative

```text
{'python_correct': True, 'python_latency_ms': 0.03, 'llm_latency_ms': 41.2}
```

## Metrics to compare

Correctness, latency, testability, and failure modes.

## Interpretation

Language models are useful for language and ambiguity. Deterministic code should handle exact rules.

## Limitations

Some tasks combine deterministic and language steps. Split them deliberately.

## Production considerations

Write unit tests for rules, especially money and permission logic.

