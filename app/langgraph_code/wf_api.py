from .workflow import build_workflow
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import logging
import hashlib

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

class LogEntry(BaseModel):
    ts: Optional[str] = None
    level: str
    message: str
    meta: Optional[dict] = None

@app.post("/log", status_code=200)
async def receive_log(entry: LogEntry):
    """Receive frontend logs and write them to server logs.

    This endpoint intentionally keeps the payload small and returns quickly. Logs are written
    to the "frontend_logs" logger which you can configure with handlers in production.
    """
    logger = logging.getLogger("frontend_logs")

    raw_msg = (entry.message or "")
    try:
        msg_bytes = raw_msg.encode("utf-8", errors="replace")
    except Exception:
        msg_bytes = b""

    msg_hash = hashlib.sha256(msg_bytes).hexdigest() if msg_bytes else None
    msg_len = len(msg_bytes)

    lvl = (entry.level or "info").lower()
    log_message = "[frontend] ts=%s level=%s msg_hash=%s msg_len=%d"
    log_params = (entry.ts or "", lvl, msg_hash or "", msg_len)

    if lvl in ("error",):
        logger.error(log_message, *log_params)
    elif lvl in ("warn", "warning"):
        logger.warning(log_message, *log_params)
    elif lvl in ("info", "log"):
        logger.info(log_message, *log_params)
    else:
        logger.debug(log_message, *log_params)
    return {"status": "ok"}