# 06. Parallel Execution

## Core idea

Run independent operations concurrently.

## Why it affects latency

Concurrency reduces idle waiting. It does not make any single service faster.

## Before implementation

Search documentation, wait, then look up account status.

## Optimized implementation

Start both operations with `asyncio.gather(..., return_exceptions=True)`.

![Sequential versus parallel execution.](../assets/sequential-vs-parallel.svg)

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.parallel_tasks
```

## Example terminal output, illustrative

```text
{'sequential_latency_ms': 204.1, 'concurrent_latency_ms': 102.7}
```

## Metrics to compare

Total runtime, success/failure of each operation, and partial-failure behavior.

## Interpretation

When operations do not depend on each other, concurrent execution can cut wall-clock time.

## Limitations

Concurrency can increase resource pressure and rate-limit exposure.

## Production considerations

Use timeouts, bounded concurrency, cancellation handling, and explicit partial-failure responses.

