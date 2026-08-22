# Contributing

Thanks for improving the latency lab. Keep changes educational, runnable in mock mode, and honest about uncertainty.

Before opening a pull request:

```bash
USE_MOCK_GEMINI=true pytest
ruff check .
ruff format --check .
mypy src
```

Guidelines:

- Do not commit secrets, `.env`, generated benchmark output, or live API responses that contain private data.
- Keep examples dependency-light and beginner-friendly.
- Do not add LangChain, LlamaIndex, SAP HANA, or proprietary vector databases.
- Avoid universal benchmark claims. Results belong to the environment where they were measured.

