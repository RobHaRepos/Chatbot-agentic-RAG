[![CI](https://github.com/RobHaRepos/Chatbot-agentic-RAG/actions/workflows/ci-build.yaml/badge.svg)](https://github.com/RobHaRepos/Chatbot-agentic-RAG/actions/workflows/ci-build.yaml) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=RobHaReposChatbotAgenticRag&metric=alert_status&token=4d160f287316ca3bbd8bdcf28b10ea3fcb540329)](https://sonarcloud.io/summary/new_code?id=RobHaReposChatbotAgenticRag) [![Snyk Vulnerabilities](https://snyk.io/test/github/RobHaRepos/Chatbot-agentic-RAG/badge.svg)](https://snyk.io/test/github/RobHaRepos/Chatbot-agentic-RAG) [![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/) ![Coverage](https://github.com/RobHaRepos/Chatbot-agentic-RAG/blob/a9a8b9919b364f59d6fcb3f19314eb4ce0eed1b5/coverage.svg)

# Chatbot-agentic-RAG

A small LangGraph-based RAG (Retrieval-Augmented Generation) demo that composes a lightweight LangGraph workflow with separate services for LLM and retriever (FAISS + HuggingFace embeddings), plus a minimal frontend. The project is organized to make the graph testable (unit and integration tests) and runnable locally or in containers.

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
  - `langgraph_code/` - LangGraph workflow and FastAPI wrapper
    - `workflow.py` - builds the StateGraph and routes actions
    - `nodes.py` - node implementations that call retriever and LLM services
    - `wf_api.py` - FastAPI wrapper for running the compiled graph (`/run`, `/health`, `/ready`)
    - `visualization.py` - (graph export/visual helpers)
  - `llm/` - LLM microservice code + API
    - `llm.py` - `AiChatService` wrapper around ChatOpenAI (generate_answer, retrieve_or_respond)
    - `llm_api.py` - FastAPI app that exposes endpoints `/retrieve_or_respond` and `/generate_answer`
    - `Dockerfile` and `docker-compose.yml` - service container for LLM
  - `rag/` - retriever microservice code
    - `embeddings.py` - simple sentence-transformers helper
    - `retriever.py` - FastAPI service using FAISS to return documents (string or list)
    - `Dockerfile` and `docker-compose.yml` - retriever container
  - `frontend/` - static single-page UI to call the workflow API
    - `index.html`, `static/app.js`, CSS and Dockerfile
- `faiss_Hugging_index/` - expected local FAISS index folder (not committed)
- `tests/` - pytest test-suite (unit + integration). Tests include monkeypatch fixtures to fake LLM and vectorstore in unit tests.
- `.github/workflows/ci-build.yaml` - CI workflow that installs deps, runs ruff, runs pytest
- `requirements.txt` - pinned Python dependencies

## How it works (high level)

1. The LangGraph workflow (`app/langgraph_code/workflow.py`) defines a tiny state machine: start -> generate_retrieve_or_respond node -> conditional branching to either retrieve, clarify, or answer nodes -> end.
2. Nodes (`app/langgraph_code/nodes.py`) are implemented as (mostly) async functions and communicate with two local microservices:
   - LLM service at `LANGGRAPH_LLM_API_URL` (default `http://localhost:8002`) — exposes `/retrieve_or_respond` and `/generate_answer`.
   - Retriever service at `LANGGRAPH_RETRIEVER_API_URL` (default `http://localhost:8001`) — exposes `/retrieve_documents_string` and `/retrieve_documents_list` backed by FAISS.
3. `app/langgraph_code/wf_api.py` exposes a FastAPI `/run` endpoint which loads the compiled graph at startup and invokes it with the posted question. The handler awaits `graph.ainvoke(payload)` so async nodes can run concurrently.

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
- Workflow (`wf_api`): `8003`

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

Notes: the LLM output format can be either plain text or a JSON-like object — for deterministic behaviour consider enforcing a JSON schema in the LLM prompt and parsing it in `app/llm/llm_api.py`.

## Visualization

The LangGraph workflow visualization is rendered to `out/stategraph.png` and shows the compiled state graph used by the workflow.

![LangGraph state graph](out/stategraph.png)

## Running locally (developer-friendly)

Prerequisites: Python 3.13, pip, optionally Docker for containerized services.

Install deps (PowerShell):

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start services in separate terminals (recommended):

- Retriever service (expects a FAISS index at `PATH_TO_FAISS_INDEX` or configure `PATH_TO_FAISS_INDEX` env var):

```powershell
# terminal 1 - retriever
$env:PATH_TO_FAISS_INDEX = "c:\path\to\faiss_Hugging_index"
uvicorn app.rag.retriever:app --host 0.0.0.0 --port 8001 --reload
```

- LLM service (requires OPENAI_API_KEY for real OpenAI calls; for unit tests the project uses fakes):

```powershell
# terminal 2 - llm
$env:OPENAI_API_KEY = "sk-..."
uvicorn app.llm.llm_api:app --host 0.0.0.0 --port 8002 --reload
```

- Workflow FastAPI (the LangGraph wrapper):

```powershell
uvicorn app.langgraph_code.wf_api:app --host 0.0.0.0 --port 8003 --reload
```

Open `app/frontend/index.html` (or run simple HTTP server or build container) and point the page to the workflow API.

Alternatively, each microservice contains a `Dockerfile` (and `docker-compose.yml` in `app/llm` and `app/rag`) to run them in containers.

## Running tests

Unit tests are written with pytest. Several tests use monkeypatching to avoid needing a real OpenAI key or FAISS index (see `tests/test_llm.py` which provides an autouse fixture that replaces `AiChatService.build_llm` with a SimpleNamespace fake).

Run tests locally (PowerShell):

```powershell
# run all tests
python -m pytest -q --maxfail=1

# run a single test
python -m pytest tests/test_llm.py::test_generate_simple_response -q
```

To generate coverage (pytest-cov is available):

```powershell
python -m pytest --cov=app --cov-report=term-missing

## Git Hooks (optional, recommended for devs)

This repo includes a pre-commit hook script under `scripts/hooks` that runs `pytest` (with coverage) and then generates `coverage.svg` using `genbadge` when tests pass.

Enable the hooks locally (versioned hooks directory):

```powershell
# make the hook executable (on Linux/macOS Git)
chmod +x scripts/hooks/pre-commit
# set the repository git hooks path
git config core.hooksPath scripts/hooks
```

Now `git commit` will run the hook and abort the commit if tests fail; if the tests pass the coverage badge is updated. `coverage.xml` is ignored via `.gitignore` but `coverage.svg` is tracked in the repo so commits will include the updated badge.

If you get `genbadge: command not found`, install it locally:

```powershell
python -m pip install -r requirements.txt
# or just install the badge tool
python -m pip install genbadge
```
```

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

Per-service Dockerfiles are located in `app/llm/`, `app/rag/`, and `app/frontend/`.

A simple approach to run everything locally with containers:
- Build and run the retriever and llm containers via their `docker-compose.yml` files
- Start the LangGraph wrapper (`wf_api`) either directly with uvicorn on the host or in another container that points to the other services by their container hostnames

Be mindful of: FAISS index volume mounting (the retriever needs access to your FAISS index folder).

## Practical tips / Known caveats

- FAISS index: the `faiss_Hugging_index` directory is expected but not committed. If you want to run the retriever service, provide a local index or mock `FAISS.load_local` in tests.
- LLM keys: unit tests avoid real OpenAI calls by monkeypatching the LLM builder. For real LLM runs, set `OPENAI_API_KEY` in the environment (or GitHub secrets for CI).
- Async nodes: the workflow invokes `await graph.ainvoke(payload)` — nodes are async and use httpx.AsyncClient. When testing, provide async-compatible fakes or monkeypatch the network layer.
- Pytest anyio setting: if you use `anyio_backend` in `pytest.ini` you may prefer to set `ANYIO_BACKEND` via environment for compatibility.
