import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.logger_service import logger_service


client = TestClient(logger_service.app)

def clear_subscribers_and_logs():
    try:
        logger_service.LOGS.clear()
    except Exception:
        pass
    try:
        logger_service._subscribers.clear()
    except Exception:
        pass

def test_post_log_and_get_logs():
    """POST to /logs stores the log and GET /logs returns it."""
    clear_subscribers_and_logs()

    payload = {
        "service": "api",
        "logger": "test_mod",
        "level": "INFO",
        "message": "test message",
        "timestamp": None,
        "extra": {}
    }

    r = client.post("/logs", json=payload)
    assert r.status_code == 201

    r = client.get("/logs")
    data = r.json()
    assert "logs" in data
    assert any(log["message"] == "test message" for log in data["logs"]) is True

def test_get_logs_filters_and_limit():
    """GET /logs can filter by service and level and honor case-insensitive level."""
    clear_subscribers_and_logs()
    client.post("/logs", json={"service": "api", "logger": "mod1", "level": "INFO", "message": "m1", "timestamp": None, "extra": {}})
    client.post("/logs", json={"service": "llm", "logger": "mod2", "level": "ERROR", "message": "m2", "timestamp": None, "extra": {}})

    r = client.get("/logs", params={"service": "llm"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["logs"]) == 1
    assert data["logs"][0]["service"] == "llm"

    r = client.get("/logs", params={"level": "error"})
    assert r.status_code == 200
    assert len(r.json()["logs"]) == 1

def test_publish_pushes_to_subscribers():
    """_publish notifies an asyncio queue subscribed to _subscribers."""
    clear_subscribers_and_logs()
    q = asyncio.Queue()
    logger_service._subscribers.append(q)

    record = {"service": "api", "logger": "t", "level": "INFO", "message": "pushed", "timestamp": datetime.now(timezone.utc).isoformat(), "extra": {}}
    asyncio.run(logger_service._publish(record))

    item = q.get_nowait()
    assert item == record
    logger_service._subscribers.remove(q)


def test_publish_multiple_subscribers():
    """_publish notifies multiple subscribers in _subscribers list."""
    clear_subscribers_and_logs()
    q1 = asyncio.Queue()
    q2 = asyncio.Queue()
    logger_service._subscribers.append(q1)
    logger_service._subscribers.append(q2)

    record = {"service": "api", "logger": "t", "level": "INFO", "message": "pushed", "timestamp": datetime.now(timezone.utc).isoformat(), "extra": {}}
    asyncio.run(logger_service._publish(record))

    assert q1.get_nowait() == record
    assert q2.get_nowait() == record

    logger_service._subscribers.remove(q1)
    logger_service._subscribers.remove(q2)


def test_stream_route_appends_subscriber_direct():
    """Calling stream_logs() directly appends an asyncio queue to _subscribers."""
    clear_subscribers_and_logs()
    resp = asyncio.run(logger_service.stream_logs())
    from fastapi.responses import StreamingResponse
    assert isinstance(resp, StreamingResponse)
    assert len(logger_service._subscribers) == 1
    logger_service._subscribers.clear()


def test_get_logs_sort_and_no_limit():
    """GET /logs sorts logs by timestamp ascending and supports limit=0 for all logs."""
    clear_subscribers_and_logs()
    client.post("/logs", json={"service": "api", "logger": "m", "level": "INFO", "message": "first", "timestamp": "2024-01-02T00:00:00+00:00", "extra": {}})
    client.post("/logs", json={"service": "api", "logger": "m", "level": "INFO", "message": "second", "timestamp": "2023-01-02T00:00:00+00:00", "extra": {}})

    r = client.get("/logs", params={"limit": 0})
    logs = r.json()["logs"]
    assert logs[0]["message"] == "second"
    assert logs[1]["message"] == "first"

def test_health_and_clear():
    """Health endpoint reports stored log count and /logs/clear clears logs."""
    clear_subscribers_and_logs()

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    client.post("/logs", json={"service": "api", "logger": "m", "level": "INFO", "message": "c1", "timestamp": None, "extra": {}})
    r = client.get("/health")
    assert r.json()["stored_logs"] >= 1

    r = client.post("/logs/clear")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    r = client.get("/logs")
    assert r.json()["logs"] == []
