import logging
import asyncio
import json
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime, timezone
from fastapi import FastAPI
from collections import deque
from typing import List , Optional, Dict, Any
from pydantic import BaseModel, Field   

logger = logging.getLogger("logger_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(service)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
app = FastAPI(title="Central Logger Service")

LOGS = deque(maxlen=10000)

_subscribers: List[asyncio.Queue] = []

class LogPayload(BaseModel):
    service: str = Field(..., description="Service name (e.g., api, llm, retriever)")
    logger: Optional[str] = Field(None, description="Loger name (e.g., module or component)")
    level: str = Field("INFO", description="Log level (e.g., INFO, ERROR)")
    message: str = Field(..., description="Log message content")
    timestamp: Optional[str] = Field(None, description="Timestamp of the log message")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional contextual information")
    
def _to_log_record(payload: LogPayload) -> Dict[str, Any]:
    record = {
        "service": payload.service if (payload.service or "") else "Missing Service",
        "logger": payload.logger if (payload.logger or "") else "Missing Logger",
        "level": payload.level.upper() if (payload.level or "") else "INFO",
        "message": payload.message if (payload.message or "") else "Missing log message",
        "timestamp": payload.timestamp if (payload.timestamp or "") else datetime.now(timezone.utc).isoformat(),
        "extra": payload.extra or {}
    }
    return record

def _emit_to_local_logger(record: Dict[str, Any]):
    try:        
        level_value = record["level"]
        if isinstance(level_value, str):
            log_level = getattr(logging, level_value.upper(), logging.INFO)
        else:
            try:
                log_level = int(level_value)
            except Exception:
                log_level = logging.INFO

        logger.log(log_level, record["message"], extra={"service": record["service"], "logger": record["logger"], "extra": record["extra"]})
    except Exception as e:
        logger.error("Failed to emit log to local logger: %s", e)
        return "Failed to emit log to local logger"

async def _publish (record: Dict[str, Any]):
    for queue in _subscribers:
        await queue.put(record)
        
@app.post("/logs", status_code=201)
async def post_log(payload: LogPayload):
    record = _to_log_record(payload)
    LOGS.append(record)
    _emit_to_local_logger(record)
    asyncio.create_task(_publish(record))
    return JSONResponse(content={"status": "ok"}, status_code=201)

@app.get("/logs")
async def get_logs(service: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    logs = list(LOGS)
    if service:
        logs = [log for log in logs if log["service"] == service]
    if level:
        level = level.upper()
        logs = [log for log in logs if log["level"] == level]
    logs.sort(key=lambda log: datetime.fromisoformat(log['timestamp']), reverse=False)
    return {"logs": logs[-limit:] if limit else logs}

@app.get("/stream")
async def stream_logs():
    async def event_generator(queue: asyncio.Queue):
        try:
            while True:
                record = await queue.get()
                yield f"data: {json.dumps(record)}\n\n"
        finally:
            try:
                _subscribers.remove(queue)
            except ValueError:
                pass
    
    queue = asyncio.Queue()
    _subscribers.append(queue)
    return StreamingResponse(event_generator(queue), media_type="text/event-stream")

@app.get("/health")
async def health_check():
    return {"status": "ok", "stored_logs": len(LOGS)}

@app.post("/logs/clear")
async def clear_logs():
    LOGS.clear()
    return {"status": "ok"}