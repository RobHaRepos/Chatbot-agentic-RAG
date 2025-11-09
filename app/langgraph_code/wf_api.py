from workflow import build_workflow
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    graph = build_workflow()
    try:
        app.state.graph = graph
        yield
    finally:
        app.state.graph = None

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8003", "http://127.0.0.1:8003", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def ready_check():
    graph = app.state.graph
    is_ready = graph is not None
    return {"status": is_ready}

class RunRequest(BaseModel):
    question: str
    k: Optional[int] = None

@app.post("/run")
async def run_workflow(request: RunRequest):
    graph = app.state.graph
    payload = {"question": request.question, "k": request.k}
    result = await graph.ainvoke(payload)
    return {"result": result}