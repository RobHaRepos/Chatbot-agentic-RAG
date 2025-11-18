from app.logger_service import logger_service
from fastapi.testclient import TestClient
import importlib
import logging

client = TestClient(logger_service.app)

def test_to_log_record_happy():
    """Happy path: _to_log_record returns expected fields for valid payload."""
    payload = logger_service.LogPayload(
        service = "api",
        logger = "test_module",
        level = "ERROR",
        message= "Test error message",
        timestamp= "2025-11-15 12:54:29,650",
        extra= {"operation": "data_fetch", "status": "failed"}
    )
    record = logger_service._to_log_record(payload)
    assert record["service"] == "api"
    assert record["logger"] == "test_module"
    assert record["level"] == "ERROR"
    assert record["message"] == "Test error message"
    assert record["timestamp"] == "2025-11-15 12:54:29,650"
    assert record["extra"]["operation"] == "data_fetch"
    assert record["extra"]["status"] == "failed"
    
def test_to_log_record_missing_information():
    """Missing fields: fallback values are provided by _to_log_record."""
    payload = logger_service.LogPayload(
        service = "",
        logger = "",
        level = "",
        message= "",
        timestamp= "",
        extra= {}
    )
    record = logger_service._to_log_record(payload)
    assert record["service"] == "Missing Service"
    assert record["logger"] == "Missing Logger"
    assert record["level"] == "INFO"
    assert record["message"] == "Missing log message"
    assert record["timestamp"] is not None and record["timestamp"].strip() != ""
    assert record["extra"] == {}
    
def test_emit_to_local_logger():
    """Emit to local logger returns an error string for invalid input."""
    error_message = logger_service._emit_to_local_logger({})
    assert error_message == "Failed to emit log to local logger"


def test_emit_to_local_logger_with_string_level(caplog):
    """Emit accepts string log levels like 'INFO' and logs correctly."""
    import logging

    caplog.set_level(logging.INFO)
    rec = {
        "service": "api",
        "logger": "test_mod",
        "level": "INFO",
        "message": "This is a log from test",
        "extra": {}
    }

    logger_service._emit_to_local_logger(rec)
    assert "This is a log from test" in caplog.text

def test_emit_to_local_logger_numeric_level(caplog):
    """_emit_to_local_logger accepts numeric logging levels and logs correctly."""
    import logging

    caplog.set_level(logging.ERROR)
    numeric_rec = {
        "service": "api",
        "logger": "test_mod",
        "level": logging.ERROR,
        "message": "Numeric log level test",
        "extra": {}
    }

    logger_service._emit_to_local_logger(numeric_rec)
    assert "Numeric log level test" in caplog.text


def test_logger_module_setup(monkeypatch):
    """Reloading module triggers logger setup branch when no handlers present."""

    fake_logger = logging.Logger("logger_service")
    monkeypatch.setattr(logging, "getLogger", lambda name=None: fake_logger)

    import app.logger_service.logger_service as ls
    importlib.reload(ls)

    assert hasattr(ls, "LOGS")