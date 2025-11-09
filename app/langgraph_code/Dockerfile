FROM python:3.13-slim
WORKDIR /app/langgraph_code

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-lg.txt /app/langgraph_code/requirements-lg.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-lg.txt

COPY . /app/langgraph_code/
ENV PORT=8000 \
    LANGGRAPH_RETRIEVER_API_URL="http://localhost:8001" \
    LANGGRAPH_LLM_API_URL="http://localhost:8002" 

EXPOSE 8000

CMD ["uvicorn", "wf_api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]