import requests
import pytest
from types import SimpleNamespace
from tests.test_retriever import _service_up

BASE_URL = "http://localhost:8002"

class TestServiceUpLlm:
    def test_service_up_happy(self, monkeypatch):
        def _fake_get(url, timeout):
            return SimpleNamespace(status_code=200)

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is True

    def test_service_up_sad(self, monkeypatch):
        def _fake_get(url, timeout):
            raise requests.RequestException("Service down")

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is False

    def test_service_up_unexpected_timeout(self, monkeypatch):
        def _fake_get(url, timeout):
            raise requests.Timeout("Timeout occurred")

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is False

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_health_endpoint():
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200
    j = resp.json()
    assert isinstance(j, dict)
    assert j.get("status") == "ok"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_ready_endpoint():
    resp = requests.get(f"{BASE_URL}/ready", timeout=5)
    assert resp.status_code == 200
    j = resp.json()
    assert isinstance(j, dict)
    assert "status" in j
    assert isinstance(j["status"], bool)

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_retrieve_or_respond_retrieve():
    payload = {"question": "What is the newest Iphone?"}
    resp = requests.post(f"{BASE_URL}/retrieve_or_respond", json=payload)
    assert resp.status_code == 200
    j = resp.json()
    assert "decision" in j
    assert j["decision"] == "retrieve"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_retrieve_or_respond_clarify():
    payload = {"question": "What is the capital of France?"}
    resp = requests.post(f"{BASE_URL}/retrieve_or_respond", json=payload)
    assert resp.status_code == 200
    j = resp.json()
    assert "decision" in j
    assert j["decision"] == "clarify"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_generate_answer_endpoint():
    payload = {
        "question": "What is the newest Iphone?",
        "context": "Iphone 16 MAX, Release: September 2024, Feature: 6.7-inch display, improved camera system."
    }
    resp = requests.post(f"{BASE_URL}/generate_answer", json=payload)
    assert resp.status_code == 200
    j = resp.json()
    assert "answer" in j
    answer = j["answer"]
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "Iphone 16 MAX".lower() in answer.lower()
    
