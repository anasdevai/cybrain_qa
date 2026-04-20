FROM python:3.11-slim

WORKDIR /app

# System deps for HuggingFace sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first (avoids downloading 2GB CUDA version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python deps (layer cache — only rebuilds when requirements change)
COPY requirements.txt requirements.db.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements.db.txt

# Copy application source
COPY . .

# HuggingFace model cache — matches named volume in docker-compose
ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 1 worker only — HF models ~220MB, multiple workers = OOM on 4GB VPS
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
