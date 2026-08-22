# 04. Context Reduction

## Core idea

Send less irrelevant context to the model.

## Why it affects latency

More input context means more data to transmit and process. It can also distract the model.

## Before implementation

Paste every support document into every prompt.

## Optimized implementation

Use local TF-IDF retrieval to select the top three passages and build a prompt with explicit separators.

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.reduce_context
```

## Example terminal output, illustrative

```text
{'all_context_chars': 1410, 'top3_context_chars': 740, 'top3_contains_expected_doc': True}
```

## Metrics to compare

Approximate context size, API input tokens, total latency, answer correctness, and evidence use.

## Interpretation

If top-k context answers the question, you can often reduce latency and improve focus.

## Limitations

TF-IDF is not a production-grade RAG system. It is used here because it is local, transparent, and dependency-light.

## Production considerations

Use stronger retrieval, access controls, citation checks, and prompt injection defenses for production.

