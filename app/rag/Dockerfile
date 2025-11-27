FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libgomp1 libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app/rag/requirements-retriever.txt /app/requirements-retriever.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-retriever.txt \
    && apt-get purge -y --auto-remove build-essential cmake git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -m -d /home/appuser -s /bin/sh appuser \
    && chown -R appuser:appuser /app \
    || true

ENV HOME=/home/appuser PYTHONUNBUFFERED=1
USER appuser

COPY app /app/app
ENV PORT=8001
EXPOSE 8001
CMD ["python", "-m", "uvicorn", "app.rag.retriever:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]