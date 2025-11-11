FROM python:3.15-rc-alpine3.22 
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY app/llm/requirements-llm.txt /app/requirements-llm.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-llm.txt

ENV PYTHONUNBUFFERED=1
COPY app /app/app
EXPOSE 8002
CMD ["python", "-m", "uvicorn", "app.llm.llm_api:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]