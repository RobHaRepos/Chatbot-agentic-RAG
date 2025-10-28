# LangGraph Frontend

This folder contains a simple static Single-Page App (SPA) that talks to the LangGraph `/run` API.

Files
- `index.html` — UI shell, includes CSS and JS.
- `static/style.css` — styles for the chat UI.
- `static/app.js` — client JS that posts to the API and renders the chat timeline.
- `Dockerfile` — container image based on nginx for production deployment.
- `docker-entrypoint.sh` — entrypoint script that injects the runtime API URL into `index.html` or writes `runtime-config.json`.

How it works
- The app expects an API base URL either substituted into `index.html` (placeholder `@@API_URL@@`) or provided via `/runtime-config.json`. The Docker entrypoint will replace the placeholder with the value of `LANGGRAPH_API_URL`, or write `runtime-config.json` with the same value.

Build and run (local, Docker)

From the repository root, build the image:

```powershell
docker build -t langgraph-frontend -f app/frontend/Dockerfile .
```

Run the container (example pointing to a LangGraph backend at `http://langgraph:8003/run`):

```powershell
docker run --rm -p 8080:80 -e LANGGRAPH_API_URL="http://langgraph:8003/run" langgraph-frontend
```

Open http://localhost:8080 in your browser.

CORS / same-origin
- If you run the frontend and API on different origins you must enable CORS on the API or use a reverse proxy so the browser can make cross-origin requests.

Runtime config pattern
- For flexible deployments you can avoid rebuilding by passing `LANGGRAPH_API_URL` at container start — the entrypoint will inject the URL into the page.

Serving static files without Docker
- To test locally without Docker, serve the `app/frontend` directory using Python:

```powershell
cd app/frontend
python -m http.server 8080
# open http://localhost:8080
```
