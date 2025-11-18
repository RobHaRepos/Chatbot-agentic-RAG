FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY app/llm/requirements-llm.txt /app/requirements-llm.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-llm.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* \
    || true

ENV PYTHONUNBUFFERED=1
COPY app /app/app
EXPOSE 8002
## Create a non-root user and set ownership of the working directory so the
## container does not run as root at runtime.
RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -m -d /home/appuser -s /bin/sh appuser \
    && chown -R appuser:appuser /app

ENV HOME=/home/appuser PYTHONUNBUFFERED=1

USER appuser

CMD ["python", "-m", "uvicorn", "app.llm.llm_api:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]