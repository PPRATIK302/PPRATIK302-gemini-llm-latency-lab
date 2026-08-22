# 01. Measuring Latency

## Core idea

Measure the latency users experience before optimizing anything.

## Why it affects latency

Without measurement, a team may optimize the wrong part of the workflow. Track total latency, TTFT for streaming, P50, P95, token counts, throughput, and error rate.

## Before implementation

Call the model once and judge speed by feel.

## Optimized implementation

Run repeated requests, record structured `LatencyRecord` rows, and summarize percentiles with `latency_lab.metrics`.

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.measure_latency
```

## Example terminal output, illustrative

```text
Requests:           5
Successful:         5
Error rate:         0.0%
P50 total latency:  151 ms
P95 total latency:  160 ms
P50 TTFT:           10 ms
P95 TTFT:           12 ms
```

## Metrics to compare

Compare P50, P95, TTFT, token counts, throughput, and failed requests.

## Interpretation

P50 shows the typical experience. P95 shows a slow-tail experience. TTFT should only be reported when streaming directly measures it.

## Limitations

Mock values are deterministic and are not Gemini infrastructure measurements.

## Production considerations

Log request IDs and safe metadata. Do not log prompts or secrets unless your privacy policy and retention controls allow it.

