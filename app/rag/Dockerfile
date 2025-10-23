FROM python:3.13-slim
WORKDIR /app/rag

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libgomp1 libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-retriever.txt /app/rag/requirements-retriever.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-retriever.txt

COPY . /app/rag/
ENV PORT=8001
EXPOSE 8001
CMD ["uvicorn", "retriever:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]