import pytest

from latency_lab.gemini_client import MockGeminiClient
from latency_lab.schemas import ClassificationResult


@pytest.mark.asyncio
async def test_structured_response_validation() -> None:
    client = MockGeminiClient(delay_ms=1)
    result, generation = await client.generate_structured(
        "Classify: duplicate invoice charge",
        model="mock",
        schema=ClassificationResult,
    )
    assert result.category == "billing"
    assert result.confidence > 0.8
    assert generation.raw == {"mock": True, "model": "mock"}


@pytest.mark.asyncio
async def test_mock_stream_chunks() -> None:
    client = MockGeminiClient(delay_ms=1, stream_delay_ms=1)
    chunks = [chunk async for chunk in client.stream("hello", model="mock", max_output_tokens=5)]
    assert chunks
    assert "".join(chunks).strip().startswith("Mock Gemini")

