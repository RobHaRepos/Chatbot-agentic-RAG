FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY app/logger_service/requirements-log.txt /app/requirements-log.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-log.txt

ENV PYTHONUNBUFFERED=1
COPY app /app/app
EXPOSE 8004
CMD ["python", "-m", "uvicorn", "app.logger_service.logger_service:app", "--host", "0.0.0.0", "--port", "8004"]

