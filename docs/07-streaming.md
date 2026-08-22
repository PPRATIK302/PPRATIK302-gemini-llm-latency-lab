# 07. Streaming

## Core idea

Stream chunks as they arrive to improve perceived responsiveness.

## Why it affects latency

The user can start reading after TTFT instead of waiting for the final token.

## Before implementation

Wait for the complete Gemini response, then return the whole string.

## Optimized implementation

Use FastAPI `StreamingResponse` and do not buffer the full upstream response first.

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.stream_response
USE_MOCK_GEMINI=true uvicorn latency_lab.api:app --reload
```

## Example terminal output, illustrative

```text
{'non_stream_total_ms': 42.1, 'stream_ttft_ms': 11.0, 'stream_total_ms': 158.4}
```

## Metrics to compare

Request start time, TTFT, and total completion time.

## Interpretation

Streaming usually improves perceived latency, while total generation time may remain similar.

## Limitations

Streaming complicates cancellation, retries, and error display.

## Production considerations

Handle client disconnects and upstream errors safely. Avoid leaking partial private data into logs.

