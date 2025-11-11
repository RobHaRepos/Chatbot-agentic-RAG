FROM python:3.15-rc-alpine3.22 
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY app/langgraph_code/requirements-lg.txt /app/requirements-lg.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-lg.txt

COPY app /app/app
ENV PORT=8000 \
    LANGGRAPH_RETRIEVER_API_URL="http://localhost:8001" \
    LANGGRAPH_LLM_API_URL="http://localhost:8002"

EXPOSE 8000

# switch to a non-root, unprivileged user for runtime.
RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -m -d /home/appuser -s /bin/sh appuser \
    && chown -R appuser:appuser /app

ENV HOME=/home/appuser PYTHONUNBUFFERED=1

USER appuser

CMD ["python", "-m", "uvicorn", "app.langgraph_code.wf_api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]