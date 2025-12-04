import hashlib
import logging

from fastapi.testclient import TestClient

from app.langgraph_code.src.wf_api import app

client = TestClient(app)


class FakeLogger:
    def __init__(self):
        self.calls = []

    def error(self, msg, *params):
        self.calls.append(("error", msg, params))

    def warning(self, msg, *params):
        self.calls.append(("warning", msg, params))

    def info(self, msg, *params):
        self.calls.append(("info", msg, params))

    def debug(self, msg, *params):
        self.calls.append(("debug", msg, params))


def _sha256_hex(b: bytes):
    return hashlib.sha256(b).hexdigest()


def test_receive_log_error_level(monkeypatch):
    """Posting error level logs routes to logger.error with hashed message metadata."""
    fake = FakeLogger()
    orig_get_logger = logging.getLogger
    monkeypatch.setattr(
        logging,
        "getLogger",
        lambda name=None, _orig=orig_get_logger: fake if name == "frontend_logs" else _orig(name),
    )

    payload = {
        "ts": "2025-11-11T00:00:00Z",
        "level": "error",
        "message": "this is an error",
        "meta": {"page": "/home"},
    }

    r = client.post("/log", json=payload)
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    assert len(fake.calls) == 1
    method, fmt, params = fake.calls[0]
    assert method == "error"
    assert "[frontend]" in fmt

    ts, lvl, msg_hash, msg_len = params
    assert ts == payload["ts"]
    assert lvl == payload["level"]
    assert msg_hash == _sha256_hex(payload["message"].encode("utf-8"))
    assert msg_len == len(payload["message"].encode("utf-8"))


def test_receive_log_warning_alias(monkeypatch):
    """Warning alias 'warn' maps to logger.warning and preserves metadata."""
    fake = FakeLogger()
    orig_get_logger = logging.getLogger
    monkeypatch.setattr(
        logging,
        "getLogger",
        lambda name=None, _orig=orig_get_logger: fake if name == "frontend_logs" else _orig(name),
    )

    payload = {"level": "warn", "message": "be careful", "meta": {}}
    r = client.post("/log", json=payload)
    assert r.status_code == 200

    assert len(fake.calls) == 1
    method, _, params = fake.calls[0]
    assert method == "warning"
    _, lvl, msg_hash, msg_len = params
    assert lvl == "warn"
    assert msg_hash == _sha256_hex(payload["message"].encode())
    assert msg_len == len(payload["message"].encode())


def test_receive_log_info_and_log_alias(monkeypatch):
    """Both 'info' and 'log' map to logger.info and include correct metadata."""
    fake = FakeLogger()
    orig_get_logger = logging.getLogger
    monkeypatch.setattr(
        logging,
        "getLogger",
        lambda name=None, _orig=orig_get_logger: fake if name == "frontend_logs" else _orig(name),
    )

    for level in ("info", "log"):
        fake.calls.clear()
        payload = {"level": level, "message": "hello", "meta": None}
        r = client.post("/log", json=payload)
        assert r.status_code == 200
        assert len(fake.calls) == 1
        method, _, params = fake.calls[0]
        assert method == "info"
        _, lvl, msg_hash, msg_len = params
        assert lvl == level
        assert msg_hash == _sha256_hex(payload["message"].encode())
        assert msg_len == len(payload["message"].encode())


def test_receive_log_unknown_level_uses_debug(monkeypatch):
    """Unknown level falls back to debug and still records the original level in metadata."""
    fake = FakeLogger()
    orig_get_logger = logging.getLogger
    monkeypatch.setattr(
        logging,
        "getLogger",
        lambda name=None, _orig=orig_get_logger: fake if name == "frontend_logs" else _orig(name),
    )

    payload = {"level": "verbose", "message": "something", "meta": {}}
    r = client.post("/log", json=payload)
    assert r.status_code == 200

    assert len(fake.calls) == 1
    method, _, params = fake.calls[0]
    assert method == "debug"
    _, lvl, msg_hash, msg_len = params
    assert lvl == "verbose"
    assert msg_hash == _sha256_hex(payload["message"].encode())
    assert msg_len == len(payload["message"].encode())


def test_receive_log_empty_message(monkeypatch):
    """An empty message results in zero-length hash and length values."""
    fake = FakeLogger()
    orig_get_logger = logging.getLogger
    monkeypatch.setattr(
        logging,
        "getLogger",
        lambda name=None, _orig=orig_get_logger: fake if name == "frontend_logs" else _orig(name),
    )

    payload = {"level": "info", "message": "", "meta": {}}
    r = client.post("/log", json=payload)
    assert r.status_code == 200

    assert len(fake.calls) == 1
    _, _, params = fake.calls[0]
    _, _, msg_hash, msg_len = params
    assert msg_hash == ""
    assert msg_len == 0