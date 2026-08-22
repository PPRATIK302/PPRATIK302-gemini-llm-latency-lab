"""Streamlit optimization dashboard."""

from __future__ import annotations

import asyncio
import os

import pandas as pd
import streamlit as st

from latency_lab.config import load_settings
from latency_lab.demos import compare_models, measure_latency
from latency_lab.metrics import summarize_records


st.set_page_config(page_title="Gemini Latency Lab", layout="wide")
st.title("Gemini LLM Latency Lab")
st.warning("Live experiments may use Gemini API quota and incur cost. Mock mode is labelled separately.")

settings = load_settings()
st.caption(f"Mode: {'mock Gemini' if settings.use_mock_gemini else 'live Gemini API'}")

experiments = ["measure_latency", "compare_models"]
experiment = st.selectbox("Experiment", experiments)
model = st.selectbox("Model", [settings.fast_model, settings.quality_model])
repetitions = st.number_input("Benchmark repetitions", min_value=1, max_value=100, value=5)
quality_threshold = st.slider("Quality threshold", 0.0, 1.0, settings.quality_threshold, 0.01)

if st.button("Run experiment", type="primary"):
    os.environ["QUALITY_THRESHOLD"] = str(quality_threshold)
    if experiment == "measure_latency":
        records = asyncio.run(measure_latency.run(repetitions=int(repetitions), model_override=model))
        summary = summarize_records(records)
        col1, col2, col3 = st.columns(3)
        col1.metric("P50 latency", f"{summary['p50_total_latency_ms']:.0f} ms")
        col2.metric("P95 latency", f"{summary['p95_total_latency_ms']:.0f} ms")
        col3.metric("P50 TTFT", "n/a" if summary["p50_ttft_ms"] is None else f"{summary['p50_ttft_ms']:.0f} ms")
        frame = pd.DataFrame([record.model_dump(mode="json") for record in records])
        st.dataframe(frame, use_container_width=True)
        st.download_button("Download CSV", frame.to_csv(index=False), "latency-results.csv", "text/csv")
        st.info("Recommendation: compare quality and latency together; do not choose a model from one run.")
    else:
        st.text(asyncio.run(compare_models.run()))
