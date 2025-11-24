[![CI](https://github.com/RobHaRepos/Chatbot-agentic-RAG/actions/workflows/ci-build.yaml/badge.svg)](https://github.com/RobHaRepos/Chatbot-agentic-RAG/actions/workflows/ci-build.yaml) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=RobHaReposChatbotAgenticRag&metric=alert_status&token=4d160f287316ca3bbd8bdcf28b10ea3fcb540329)](https://sonarcloud.io/summary/new_code?id=RobHaReposChatbotAgenticRag) [![Snyk Vulnerabilities](https://snyk.io/test/github/RobHaRepos/Chatbot-agentic-RAG/badge.svg)](https://snyk.io/test/github/RobHaRepos/Chatbot-agentic-RAG) [![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/) ![Coverage](https://raw.githubusercontent.com/RobHaRepos/Chatbot-agentic-RAG/main/coverage.svg)

# Chatbot-agentic-RAG

A small LangGraph-based RAG (Retrieval-Augmented Generation) demo composed of small, single-purpose services:
an LLM microservice, a FAISS retriever, a minimal frontend, and a central logging service with SSE support. The code is organized for easy local development (uvicorn and Docker Compose), robust testing (unit + integration with pytest), and per-service dependency management.

## Quick overview

- Language: Python 3.13
- Web framework: FastAPI
- Orchestration: LangGraph StateGraph (small compiled graph) for workflow logic
- Retrieval: FAISS vector store + HuggingFace sentence-transformers
- LLM: langchain_openai ChatOpenAI wrapper (AiChatService)
- Frontend: minimal static HTML/JS to call the workflow API
- Testing: pytest (with a number of unit tests that use monkeypatching to avoid external services)
- CI: GitHub Actions workflow defined in `.github/workflows/ci-build.yaml`

## Repo structure (short)

- `app/` - application services and code
  - `config.py` - common config defaults and constants (paths, model names, tokens)
  - `logger_service/` - centralized log collector
    - `logger_service.py` - FastAPI minimal logging API (POST /logs, GET /logs, SSE /stream)
    - `handlers.py` - `HTTPLogHandler` used by services to forward logs
    - `Dockerfile`, `requirements-log.txt` - container configuration and deps
  - `langgraph_code/` - LangGraph workflow and FastAPI wrapper
    - `workflow.py` - builds the StateGraph and routes actions
    - `nodes.py` - node implementations that call retriever and LLM services
    - `wf_api.py` - FastAPI wrapper for running the compiled graph (`/run`, `/health`, `/ready`)
    - `visualization.py` - (graph export/visual helpers)
  - `llm/` - LLM microservice code + API
    - `llm.py` - `AiChatService` wrapper around ChatOpenAI (generate_answer, retrieve_or_respond)
    - `llm_api.py` - FastAPI app that exposes endpoints `/retrieve_or_respond` and `/generate_answer`
    - `Dockerfile`, `requirements-llm.txt` - service container and per-service dependencies
  - `rag/` - retriever microservice code
    - `embeddings.py` - simple sentence-transformers helper
    - `retriever.py` - FastAPI service using FAISS to return documents (string or list)
    - `Dockerfile`, `requirements-retriever.txt` - retriever container and per-service deps
  - `frontend/` - static single-page UI to call the workflow API
    - `index.html`, `static/app.js`, CSS and Dockerfile
- `faiss_Hugging_index/` - expected local FAISS index folder (not committed)
- `tests/` - pytest test-suite (unit + integration). Tests include monkeypatch fixtures to fake LLM and vectorstore in unit tests.
 
- `docker-compose.yml` - top-level compose that wires service envs (e.g., `LOGGER_SERVICE_URL` and `SERVICE_NAME`) and healthchecks
- `.github/workflows/ci-build.yaml` - CI workflow that installs deps, runs ruff and pytest
- `requirements.txt` - pinned Python dependencies (per-service requirement files are in each microservice folder: `requirements-llm.txt`, `requirements-retriever.txt`, `requirements-log.txt`, `requirements-lg.txt`)

## How it works (high level)

1. The LangGraph workflow (`app/langgraph_code/workflow.py`) defines a compact state machine that starts by invoking the `generate_retrieve_or_respond` node; the return action (retrieve, clarify, answer) routes the flow to subsequent nodes and eventually ends. The graph is intentionally small so it is easy to reason about the RAG loop.
2. Nodes (`app/langgraph_code/nodes.py`) are implemented as (mostly) async handlers and call two local microservices:
  - LLM service at `LANGGRAPH_LLM_API_URL` (default `http://localhost:8002`) — exposes `/retrieve_or_respond` (decide next action) and `/generate_answer` (produce answers); these endpoints are the primary drivers for deciding when to retrieve or return a final answer.
  - Retriever service at `LANGGRAPH_RETRIEVER_API_URL` (default `http://localhost:8001`) — exposes `/retrieve_documents_string` and `/retrieve_documents_list` and is backed by the FAISS index; nodes call retriever when the LLM asks for additional information.
3. `app/langgraph_code/wf_api.py` exposes a FastAPI `/run` endpoint that loads the compiled graph at startup and invokes it with the posted question; the handler awaits `graph.ainvoke(payload)` so async nodes can run concurrently and the workflow can return a single `OverallState` that contains `action`, `documents`, `context`, `answer`, and `retrieval_counter`.
4. Logging and observability: the repository provides a centralized logger service (`app/logger_service`) and `HTTPLogHandler` that module code can attach to push logs to `LOGGER_SERVICE_URL`. The logger stores and exposes logs via `GET /logs` and `GET /stream` (SSE), which is useful for live-tail debugging during local development or in containers.

## LLM-driven retrieval and iterative context

- **LLM decides when to retrieve:** The LLM (via the `AiChatService`) evaluates whether the current retrieved documents and existing context provide enough information to answer the user's question fully. If the model determines additional information is needed, it returns an action that triggers another targeted retrieval from the vectorstore. This enables multi-step retrievals where the LLM asks for focused data rather than returning partial or uncertain answers.

- **Context is maintained and summarized:** Each time the LLM requests another retrieval or generates an answer, it may also produce an updated `context` — a short, summarized string representing aggregated information relevant to the user's multi-part question. The workflow stores and passes this `context` in the shared `OverallState` across iterations.

- **Where to find the context and action:** The final `OverallState` returned by the workflow (the `result` key in the `/run` response) includes fields like `action`, `answer`, `documents`, and `context`. For example, the FastAPI `/run` endpoint returns `{"result": <OverallState dict>}` where `result["context"]` contains the LLM-maintained context and `result["retrieval_counter"]` tracks how many retrieval iterations occurred.

- **Why this helps:** This design keeps retrievals focused (reducing unnecessary vector searches), allows the LLM to iteratively refine queries, and makes the workflow resilient to partial or inconsistent document coverage by explicitly tracking what has already been gathered in `context`.

- **Safety limit on iterations:** To avoid infinite retrieve/answer loops the workflow stops iterative retrieval after a small number of retrievals. The implementation uses `retrieval_counter` in the `OverallState` and the nodes will stop requesting further retrievals after 5 retrieval iterations (the code checks if the counter is greater than 4 and then asks for clarification instead). You can inspect or adjust this behavior in `app/langgraph_code/nodes.py`.

## Environment variables (short)

- `PATH_TO_FAISS_INDEX` - path to FAISS index used by the retriever service.
- `OPENAI_API_KEY` - optional; required for real OpenAI calls in the LLM service.
- `LANGGRAPH_LLM_API_URL` (default `http://localhost:8002`) - where the workflow calls the LLM.
- `LANGGRAPH_RETRIEVER_API_URL` (default `http://localhost:8001`) - where the workflow calls the retriever.
- `MODEL_NAME_LLM`, `TEMPERATURE_LLM`, `MAX_TOKENS` - LLM tuning variables used by `AiChatService`.

Default service ports used by the examples in this README:
 - Retriever: `8001`
 - LLM: `8002`
 - Workflow (`wf_api`): `8000`
 - Frontend: `8003`
 - Logger: `8004`

## API reference (minimal)

- **Workflow (LangGraph wrapper)**
  - `POST /run` - body: `{"question": "...", "k": <int?>}` -> returns `{"result": <OverallState dict>}`. `result` contains fields: `question`, `query`, `k`, `action`, `context`, `answer`, `documents`, `retrieval_counter`.
  - `GET /health` -> `{"status": "ok"}`
  - `GET /ready` -> `{"status": <bool>}` (graph loaded at startup)

- **LLM service** (`app/llm/llm_api.py`)
  - `POST /retrieve_or_respond` - body: `{"question": "..."}` -> returns JSON like `{"action": "retrieve"}` or `{"action": "clarify", "answer": "..."}`.
  - `POST /generate_answer` - body: `{"question": "...", "documents": "...", "context": "..."}` -> returns either a string answer or a small JSON object (the code attempts to parse JSON-like responses). Tests normalize this value before asserting.

- **Retriever service** (`app/rag/retriever.py`)
  - `POST /retrieve_documents_string` - body: `{"query": "...", "k": <int?>}` -> returns `{"documents": "<concatenated string>"}` (used by nodes to populate `state['documents']`).

## Visualization

The LangGraph workflow visualization is rendered to `out/stategraph.png` and shows the compiled state graph used by the workflow.

![LangGraph state graph](out/stategraph.png)

## Running tests

Unit tests use pytest (+ coverage) with monkeypatching to avoid external services. For example `tests/test_llm.py` replaces `AiChatService.build_llm` with a simple fake.

## CI / CD

This repository includes a GitHub Actions workflow at `.github/workflows/ci-build.yaml` that:
- checks out the code
- sets up Python 3.13
- installs dependencies from `requirements.txt`
- runs `ruff check .` (requires `ruff` present in the environment)
- runs `pytest`

The tests badge at the top links to that workflow run.

## Security scanning (Snyk / SonarQube)

This repo leverages external scanning-as-a-service for testing and reporting during development:

- Snyk: the project uses the Snyk website/service for dependency vulnerability scanning and occasional scans run from CI. You can connect the repository to Snyk to get automated PR alerts for vulnerable libraries.

- SonarQube Cloud: for code-quality and security hotspot analysis I use SonarQube Cloud to run analysis and track issues over time. 

## Dockerization / Containers

Per-service Dockerfiles are located in `app/llm/`, `app/rag/`, `app/frontend/` and `app/logger_service/` (central logger).

Security and runtime notes:

- Each service runs as a non-root `appuser` user when the container starts to reduce exposure to privilege escalation in the container runtime.
- Build-only packages (e.g., `build-essential`, `cmake`) are removed after Python dependencies are installed in the Dockerfiles to minimize the image footprint and surface area.

A simple approach to run everything locally with containers (recommended):

- Build images and bring up the full stack with Docker Compose (Compose v2):

```powershell
# Rebuild all images (no cache recommended during development when editing Dockerfiles)
docker compose build --no-cache --pull

# Start the full stack
docker compose up -d
```

- Compose wires service envs such as `LOGGER_SERVICE_URL` and `SERVICE_NAME` so services can post logs and be identified by the central logger. `docker-compose.yml` maps service ports to the host (e.g., retriever:8001, llm:8002, frontend:8003, logger:8004).

- The `faiss_Hugging_index` folder is mounted as a volume into the retriever container (read-only) in Compose; be sure to provide it locally or mount a different directory when running the retriever.

- Verify services are healthy and responding:

```powershell
docker compose ps  # shows service states
docker compose logs llm --tail 100
docker compose logs retriever --tail 100
docker compose logs logger_service --tail 200
```

Quick health checks (from host):

```powershell
curl http://localhost:8004/health   # central logger
curl http://localhost:8001/health   # retriever
curl http://localhost:8002/health   # llm
curl http://localhost:8000/health   # workflow
```

## Logging service (centralized)

The repo includes a small centralized logging service (`app/logger_service`) with a simple API for other services to POST logs and stream them for live tailing.

Key endpoints: `POST /logs`, `GET /logs`, `GET /stream` (SSE), `POST /logs/clear`, and `GET /health`.
