# CricChat API — for App Runner / ECR
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
COPY rag/requirements.txt rag/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r rag/requirements.txt

COPY backend/ backend/
COPY rag/ rag/

ENV XDG_CACHE_HOME=/app/.cache
RUN python rag/01_build_chroma.py

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
