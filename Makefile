.PHONY: install test lint format api dashboard demo benchmark

install:
	python -m pip install -r requirements-dev.txt

test:
	USE_MOCK_GEMINI=true pytest

lint:
	ruff check .
	ruff format --check .
	mypy src

format:
	ruff format .
	ruff check --fix .

api:
	USE_MOCK_GEMINI=true uvicorn latency_lab.api:app --reload

dashboard:
	USE_MOCK_GEMINI=true streamlit run dashboard/app.py

demo:
	USE_MOCK_GEMINI=true python scripts/run_all_demos.py

benchmark:
	USE_MOCK_GEMINI=true python scripts/run_benchmark.py

