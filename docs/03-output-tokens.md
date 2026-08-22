# 03. Output Tokens

## Core idea

Generate only the fields your application needs.

## Why it affects latency

After the first token, the model still needs time to generate every remaining token. Shorter valid output often reduces completion time.

## Before implementation

Ask for a detailed explanation when the application only needs a category.

## Optimized implementation

Ask for compact structured JSON validated by `ClassificationResult`.

## How to run the example

```bash
USE_MOCK_GEMINI=true python -m latency_lab.demos.limit_output
```

## Example terminal output, illustrative

```text
{'unrestricted_output_tokens': 21, 'constrained_output_tokens': 4, 'structured_valid': True}
```

## Metrics to compare

Output tokens, total latency, response validity, and task accuracy.

## Interpretation

Short output is faster only when it still contains everything downstream code requires.

## Limitations

Some tasks need explanations, citations, or multi-step reasoning output.

## Production considerations

Use schemas where supported. Validate every response before trusting it.

