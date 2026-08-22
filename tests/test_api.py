import pytest
from httpx import ASGITransport, AsyncClient

from latency_lab.api import app


@pytest.mark.asyncio
async def test_health_does_not_require_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_GEMINI", "true")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_generate_validates_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_GEMINI", "true")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/generate", json={"prompt": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_mock_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_GEMINI", "true")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/generate/stream", json={"prompt": "hello", "max_output_tokens": 8})
    assert response.status_code == 200
    assert "Mock Gemini" in response.text

