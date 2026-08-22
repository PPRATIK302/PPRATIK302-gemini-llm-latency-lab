FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src
ENV USE_MOCK_GEMINI=true
EXPOSE 8000
CMD ["uvicorn", "latency_lab.api:app", "--host", "0.0.0.0", "--port", "8000"]

