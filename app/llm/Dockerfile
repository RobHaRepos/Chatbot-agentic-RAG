FROM python:3.13-slim
WORKDIR /app/llm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-llm.txt /app/llm/requirements-llm.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-llm.txt

ENV PYTHONUNBUFFERED=1
COPY . /app/llm/
EXPOSE 8002
CMD ["uvicorn", "llm_api:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]