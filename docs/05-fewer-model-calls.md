# 05. Fewer Model Calls

## Core idea

Collapse sequential calls when one structured call can return all required fields.

## Why it affects latency

Sequential model calls add round-trip time and force later calls to wait for earlier calls.

## Before implementation

Call Gemini for intent, then call it again for query rewriting, then call it again for a retrieval decision.

## Optimized implementation

Ask for one JSON object containing `intent`, `search_query`, and `requires_retrieval`.

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.combine_calls
```

## Example terminal output, illustrative

```text
{'sequential_calls': 3, 'combined_calls': 1, 'combined_valid': True}
```

## Metrics to compare

Number of calls, total latency, output validity, and workflow accuracy.

## Interpretation

Combining calls helps when the fields share the same permissions, quality requirement, and retry behavior.

## Limitations

Separate calls can still be correct when steps have different security boundaries or failure policies.

## Production considerations

Keep separate calls for high-risk steps, different models, tool permissions, or independent retry strategies.

