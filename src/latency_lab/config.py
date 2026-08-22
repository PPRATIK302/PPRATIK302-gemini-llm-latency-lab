"""Configuration loading for the latency lab."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Runtime settings read from environment variables."""

    gemini_api_key: str | None
    fast_model: str
    quality_model: str
    use_mock_gemini: bool
    mock_delay_ms: int
    mock_stream_delay_ms: int
    mock_fail_experiment: str | None
    timeout_seconds: float
    quality_threshold: float
    results_dir: Path


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """Load settings without triggering any API calls."""

    load_dotenv()
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        fast_model=os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash-lite"),
        quality_model=os.getenv("GEMINI_QUALITY_MODEL", "gemini-2.5-flash"),
        use_mock_gemini=_bool(os.getenv("USE_MOCK_GEMINI"), default=False),
        mock_delay_ms=int(os.getenv("MOCK_GEMINI_DELAY_MS", "40")),
        mock_stream_delay_ms=int(os.getenv("MOCK_GEMINI_STREAM_DELAY_MS", "10")),
        mock_fail_experiment=os.getenv("MOCK_GEMINI_FAIL_EXPERIMENT") or None,
        timeout_seconds=float(os.getenv("GEMINI_TIMEOUT_SECONDS", "30")),
        quality_threshold=float(os.getenv("QUALITY_THRESHOLD", "0.90")),
        results_dir=ROOT / "results",
    )

