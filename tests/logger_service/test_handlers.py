import logging
import time
from unittest.mock import MagicMock

from app.logger_service.handlers import HTTPLogHandler

def make_log_record(msg: str, level=logging.INFO):
    # Create a LogRecord instance; needed for logger.emit
    return logging.LogRecord(name="test", level=level, pathname=__file__, lineno=1, msg=msg, args=(), exc_info=None)

def test_emit_enqueues_payload():
    """Emit should put the formatted payload into the handler's queue."""
    handler = HTTPLogHandler("http://localhost:8004", queue_size=10)
    handler._stopped.set()

    record = make_log_record("hello world")
    handler.emit(record)

    assert handler._queue.qsize() == 1

    handler._stopped.set()
    handler._worker.join(timeout=1)


def test_emit_includes_extra_and_service_env(monkeypatch):
    """Emit should pull 'SERVICE_NAME' env and include 'extra' fields in payload."""
    handler = HTTPLogHandler("http://localhost:8004", queue_size=10)
    handler._stopped.set()

    rec = make_log_record("hello world")
    rec.extra = {"operation": "data_fetch"}

    monkeypatch.setenv("SERVICE_NAME", "test_service")
    handler.emit(rec)

    assert handler._queue.qsize() == 1
    payload = handler._queue.get_nowait()
    assert payload["extra"]["operation"] == "data_fetch"
    assert payload["service"] == "test_service"

    handler._stopped.set()
    handler._worker.join(timeout=1)


def test_emit_default_service_name_when_not_set(monkeypatch):
    """Emit uses 'unknown' as the default service name when SERVICE_NAME is missing."""
    handler = HTTPLogHandler("http://localhost:8004", queue_size=10)
    handler._stopped.set()

    rec = make_log_record("hello world")
    handler.emit(rec)

    payload = handler._queue.get_nowait()
    assert payload["service"] == "unknown"

    handler._stopped.set()
    handler._worker.join(timeout=1)

def test_worker_appends_logs_only_once(monkeypatch):
    """Worker should POST to a single '/logs' endpoint regardless of trailing slash."""
    called = []

    def fake_post(self, url, json=None, timeout=None):
        called.append(url)
        handler._stopped.set()
        return MagicMock(status_code=200)

    monkeypatch.setattr("requests.Session.post", fake_post)
    handler = HTTPLogHandler("http://logger:8004/logs", queue_size=10)
    handler.emit(make_log_record("test working"))

    timeout = 2
    start = time.time()
    while not called and (time.time() - start) < timeout:
        time.sleep(0.01)

    assert called, "No requests were made by the worker"
    assert called[0].endswith("/logs")
    assert not called[0].endswith("/logs/logs")

    handler._stopped.set()
    handler._worker.join(timeout=1)

def test_worker_reports_non_2xx(monkeypatch, capsys):
    """Worker should write diagnostic to stderr when the POST returns non-2xx status code."""
    def fake_post(self, url, json=None, timeout=None):
        handler._stopped.set()
        return MagicMock(status_code=500)

    monkeypatch.setattr("requests.Session.post", fake_post)

    handler = HTTPLogHandler("http://localhost:8004", queue_size=10)
    handler.emit(make_log_record("should report error"))

    timeout = 2
    start = time.time()
    stderr_output = ""
    while (time.time() - start) < timeout:
        captured = capsys.readouterr()
        stderr_output += captured.err
        if "Failed to send log to central logger" in stderr_output:
            break
        time.sleep(0.01)

    assert "Failed to send log to central logger" in stderr_output

    handler._stopped.set()
    handler._worker.join(timeout=1)


def test_emit_handles_queue_full_and_empty(monkeypatch):
    """Emit should handle queue.Full by dropping oldest and inserting new payload."""
    handler = HTTPLogHandler("http://localhost:8004", queue_size=1)
    handler._stopped.set()

    handler._queue.put_nowait({"dummy": True})

    record = make_log_record("filling queue")
    handler.emit(record)
    assert handler._queue.qsize() == 1

    handler._stopped.set()
    handler._worker.join(timeout=1)


def test_emit_calls_handle_error_on_unexpected_exception(monkeypatch):
    """Emit should call handleError when queue put fails with an unexpected error."""
    handler = HTTPLogHandler("http://localhost:8004", queue_size=10)
    handler._stopped.set()

    def broken_put(item):
        raise RuntimeError("boom")

    monkeypatch.setattr(handler._queue, "put_nowait", broken_put)

    called = {"handled": False}

    def fake_handle_error(r):
        called["handled"] = True

    monkeypatch.setattr(handler, "handleError", fake_handle_error)

    handler.emit(make_log_record("should trigger handleError"))
    assert called["handled"] is True

    handler._stopped.set()
    handler._worker.join(timeout=1)
