# Interpreting Results

## Core idea

Benchmark results describe one run in one environment.

## Why it affects latency

Network path, region, account limits, model load, prompt caching, response length, and retries can all change measured latency.

## Before implementation

Treat one run as proof that a model or prompt is always faster.

## Optimized implementation

Repeat runs, save results, compare distributions, and keep quality metrics next to latency metrics.

## How to run the example

```bash
USE_MOCK_GEMINI=true python scripts/run_benchmark.py
python scripts/create_charts.py
```

## Example terminal output, illustrative

```text
P50 total latency:  1240 ms
P95 total latency:  2410 ms
P50 TTFT:           410 ms
P95 TTFT:           780 ms
```

## Metrics to compare

P50, P95, TTFT, input tokens, output tokens, quality score, failed requests, and throughput.

## Interpretation

Look for bottlenecks before choosing a fix. A token reduction fix helps a different problem than a sequential-call fix.

## Limitations

Mock results validate code paths, not real Gemini performance.

## Production considerations

Use environment metadata, privacy controls, and clear cost tracking for live benchmarks.

