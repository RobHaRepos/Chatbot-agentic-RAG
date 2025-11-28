from fastapi.testclient import TestClient
import requests
import pytest
from types import SimpleNamespace
from app.llm import llm_api
from tests.rag.test_retriever import _service_up


client = TestClient(llm_api.app)
BASE_URL = "http://localhost:8002"


def test_retrieve_or_respond(monkeypatch):
    """POST /retrieve_or_respond proxies to llm_service.retrieve_or_respond."""
    monkeypatch.setattr(llm_api.llm_service, "retrieve_or_respond", lambda user_input: {"action": "retrieve"})
    r = client.post("/retrieve_or_respond", json={"question": "test"})
    assert r.status_code == 200
    assert r.json()["action"] == "retrieve"


def test_generate_answer_empty_question():
    """POST /generate_answer returns a friendly message if question is empty."""
    r = client.post("/generate_answer", json={"question": ""})
    assert r.status_code == 200
    assert "need a question" in r.json()["answer"]


def test_generate_answer_returns_json_string(monkeypatch):
    """Endpoint parses JSON-string output from AiChatService into dicts."""
    monkeypatch.setattr(llm_api.llm_service, "generate_answer", lambda user_input, retrieved_information, context: "{\"action\": \"clarify\", \"answer\": \"please clarify\"}")
    r = client.post("/generate_answer", json={"question": "x", "documents": "", "context": ""})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
    assert r.json()["action"] == "clarify"


def test_generate_answer_returns_plain_string(monkeypatch):
    """Endpoint returns a plain string if LLM returns non-JSON text."""
    monkeypatch.setattr(llm_api.llm_service, "generate_answer", lambda user_input, retrieved_information, context: "Plain answer")
    r = client.post("/generate_answer", json={"question": "x", "documents": "", "context": ""})
    assert r.status_code == 200
    assert isinstance(r.json(), str)


def test_readiness_and_health(monkeypatch):
    """Readiness depends on llm_service.llm; health returns 'ok'."""
    class Dummy:
        llm = "present"

    monkeypatch.setattr(llm_api.llm_service, "llm", Dummy())
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] is True

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readiness_false_when_no_llm(monkeypatch):
    """Readiness returns False when llm attribute is None."""
    monkeypatch.setattr(llm_api.llm_service, "llm", None)
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] is False

class TestServiceUpLlm:
    def test_service_up_happy(self, monkeypatch):
        """_service_up returns True for 200 responses."""
        def _fake_get(url, timeout):
            return SimpleNamespace(status_code=200)

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is True

    def test_service_up_sad(self, monkeypatch):
        """_service_up returns False if an exception is raised by requests.get."""
        def _fake_get(url, timeout):
            raise requests.RequestException("Service down")

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is False

    def test_service_up_unexpected_timeout(self, monkeypatch):
        """_service_up returns False on Timeout exception."""
        def _fake_get(url, timeout):
            raise requests.Timeout("Timeout occurred")

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is False

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_health_endpoint():
    """Integration test: LLM service /health endpoint responds ok when available."""
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200
    j = resp.json()
    assert isinstance(j, dict)
    assert j.get("status") == "ok"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_ready_endpoint():
    """Integration test: LLM service /ready endpoint returns boolean status."""
    resp = requests.get(f"{BASE_URL}/ready", timeout=5)
    assert resp.status_code == 200
    j = resp.json()
    assert isinstance(j, dict)
    assert "status" in j
    assert isinstance(j["status"], bool)

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_retrieve_or_respond_retrieve():
    """Integration: /retrieve_or_respond returns retrieve action when appropriate."""
    payload = {"question": "What is the newest Iphone?"}
    resp = requests.post(f"{BASE_URL}/retrieve_or_respond", json=payload)
    assert resp.status_code == 200
    j = resp.json()
    assert "action" in j
    assert j["action"] == "retrieve"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_retrieve_or_respond_clarify():
    """Integration: /retrieve_or_respond returns clarify for non phone queries."""
    payload = {"question": "What is the capital of France?"}
    resp = requests.post(f"{BASE_URL}/retrieve_or_respond", json=payload)
    assert resp.status_code == 200
    j = resp.json()
    assert "action" in j
    assert j["action"] == "clarify"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="LLM service is not running")
def test_generate_answer_endpoint():
    """Integration: /generate_answer returns an LLM-generated string answer."""
    payload = {
        "question": "What is the newest Iphone?",
        "context": "Iphone 16 MAX, Release: September 2024, Feature: 6.7-inch display, improved camera system."
    }
    resp = requests.post(f"{BASE_URL}/generate_answer", json=payload)
    assert resp.status_code == 200
    answer = resp.json()
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "Iphone 16 MAX".lower() in answer.lower()
    
