FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY app/logger_service/requirements-log.txt /app/requirements-log.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-log.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* \
    || true

COPY app /app/app
EXPOSE 8004

# switch to a non-root, unprivileged user for runtime.
RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -m -d /home/appuser -s /bin/sh appuser \
    && chown -R appuser:appuser /app

ENV HOME=/home/appuser PYTHONUNBUFFERED=1
USER appuser

CMD ["python", "-m", "uvicorn", "app.logger_service.logger_service:app", "--host", "0.0.0.0", "--port", "8004"]

