"""Pydantic schemas shared by demos and the API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Category = Literal["billing", "technical", "account", "general"]


class LatencyRecord(BaseModel):
    request_id: str
    experiment: str
    model: str
    started_at: datetime
    ttft_ms: float | None
    total_latency_ms: float
    input_tokens: int | None
    output_tokens: int | None
    success: bool
    error_type: str | None
    quality_score: float | None


class GenerationResult(BaseModel):
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict[str, object] | None = None


class ClassificationResult(BaseModel):
    category: Category
    confidence: float = Field(ge=0.0, le=1.0)


class WorkflowPlan(BaseModel):
    intent: Category
    search_query: str
    requires_retrieval: bool


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=256, ge=1, le=4096)


class GenerateResponse(BaseModel):
    request_id: str
    model: str
    text: str
    record: LatencyRecord


class BenchmarkRequest(BaseModel):
    experiment: str = Field(default="measure_latency", max_length=80)
    prompt: str = Field(default="Classify this support request: I cannot sign in.", max_length=8000)
    repetitions: int = Field(default=5, ge=1, le=100)
    model: str | None = None
    stream: bool = False


class BenchmarkResponse(BaseModel):
    request_id: str
    summary: dict[str, float | int | None]
    records: list[LatencyRecord]


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    model: str | None = None


class RouteResponse(BaseModel):
    request_id: str
    result: ClassificationResult
    model_used: str
    escalated: bool

