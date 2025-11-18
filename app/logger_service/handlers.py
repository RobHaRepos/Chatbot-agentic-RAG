import logging
import queue
import threading
import os
import requests
from datetime import datetime, timezone

class HTTPLogHandler(logging.Handler):
    def __init__(self, url: str, timeout: float = 2.0, queue_size: int = 1000):
        super().__init__()
        self.url = url
        self.timeout = timeout
        self._queue = queue.Queue(maxsize=queue_size)
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._stopped = threading.Event()
        self._worker.start()
        
    def emit(self, record: logging.LogRecord):
        payload = None
        try:
            extra_data = getattr(record, "extra", {}) or {}
            payload = {
                "service": getattr(record, "service", os.getenv("SERVICE_NAME", "unknown")),
                "logger": record.name,
                "level": record.levelname,
                "message": self.format(record),
                "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                "extra": dict(extra_data.items()),
            }
            self._queue.put_nowait(payload)
        except queue.Full:
            try:
                _ = self._queue.get_nowait()
                if payload is not None:
                    self._queue.put_nowait(payload)
            except queue.Empty:
                pass
        except Exception:
            self.handleError(record)
        
    def _worker_loop(self):
        session = requests.Session()
        while not self._stopped.is_set():
            try:
                payload = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                endpoint = self.url
                if not endpoint.endswith("/logs"):
                    endpoint = endpoint.rstrip("/") + "/logs"

                r = session.post(endpoint, json=payload, timeout=self.timeout)
                if not (200 <= r.status_code < 300):
                    print(f"Failed to send log to central logger, status={r.status_code}: {payload}")
            except Exception:
                print("Failed to send log to central logger: ", payload)
            finally:
                self._queue.task_done()
