"""Demo 4: send less irrelevant context."""

from __future__ import annotations

import asyncio

from latency_lab.config import ROOT, load_settings
from latency_lab.gemini_client import build_client
from latency_lab.metrics import perf_ms
from latency_lab.retrieval import (
    LocalTfidfRetriever,
    approximate_context_size,
    build_safe_prompt,
    contains_evidence,
    load_documents,
)


async def run() -> dict[str, object]:
    settings = load_settings()
    client = build_client(settings)
    documents = load_documents(ROOT / "data" / "sample_documents.json")
    retriever = LocalTfidfRetriever(documents)
    question = "How do I rotate an API token safely?"
    all_passages = retriever.search(question, top_k=len(documents))
    top_passages = retriever.search(question, top_k=3)

    all_prompt = build_safe_prompt(question, all_passages)
    top_prompt = build_safe_prompt(question, top_passages)

    start = perf_ms()
    all_result = await client.generate(all_prompt, model=settings.fast_model)
    all_ms = perf_ms() - start
    start = perf_ms()
    top_result = await client.generate(top_prompt, model=settings.fast_model)
    top_ms = perf_ms() - start
    return {
        "all_context_chars": approximate_context_size(all_prompt),
        "top3_context_chars": approximate_context_size(top_prompt),
        "all_input_tokens": all_result.input_tokens,
        "top3_input_tokens": top_result.input_tokens,
        "all_latency_ms": round(all_ms, 1),
        "top3_latency_ms": round(top_ms, 1),
        "top3_contains_expected_doc": any(p.document.id == "DOC-004" for p in top_passages),
        "top3_answer_contains_evidence": contains_evidence(top_result.text, top_passages),
    }


async def main() -> None:
    print(await run())


if __name__ == "__main__":
    asyncio.run(main())

