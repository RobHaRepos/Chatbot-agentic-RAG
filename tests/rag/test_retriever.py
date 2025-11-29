from types import SimpleNamespace
import requests
import pytest
import logging
import app.rag.src.retriever as retriever_module
from fastapi.testclient import TestClient

from app.logger_service.handlers import HTTPLogHandler as _HTTPLogHandler
from typing import cast

BASE_URL = "http://localhost:8001"
PAYLOAD = {
    "query": "What are the newest Iphones?",
    "k": 10
}

@pytest.fixture
def fake_vector_store(monkeypatch):
    """Provide a fake FAISS-like vector store for unit tests."""
    class FakeRetriever:
        def invoke(self, query):
            return [
                SimpleNamespace(page_content="Doc A"),
                SimpleNamespace(page_content="Doc B"),
            ]
    fake_store = SimpleNamespace(as_retriever=lambda *a, **k: FakeRetriever())

    monkeypatch.setattr(retriever_module, "vector_store", fake_store, raising=False)

    import langchain_huggingface
    class CheapEmb:
        def __init__(self, model_name=None, **kwargs):
            # Stub to avoid loading real embedding models in tests
            pass
    monkeypatch.setattr(langchain_huggingface, "HuggingFaceEmbeddings", CheapEmb)

    return fake_store

@pytest.fixture
def test_client(monkeypatch):
    """Create test client with mocked dependencies."""
    # Mock FAISS and embeddings
    monkeypatch.setattr(
        retriever_module.FAISS,
        "load_local",
        lambda *a, **k: SimpleNamespace(as_retriever=lambda **x: SimpleNamespace(invoke=lambda q: [])),
    )
    monkeypatch.setattr(retriever_module, "embeddings", SimpleNamespace(), raising=False)
    monkeypatch.setattr(retriever_module, "vector_store", SimpleNamespace(), raising=False)

    # Mock database functions
    monkeypatch.setattr(retriever_module, "init_db", lambda: None)
    monkeypatch.setattr(retriever_module, "seed_embedding_models", lambda: None)
    monkeypatch.setattr(retriever_module, "seed_default_store", lambda: None)

    return TestClient(retriever_module.app)

def _service_up(url: str) -> bool:
    """Return True when the retriever service health endpoint is reachable and OK."""
    try:
        r = requests.get(f"{url}/health", timeout=2)
        return r.status_code == 200
    except requests.RequestException:
        return False

class TestServiceUpRetriever:
    def test_service_up_happy(self, monkeypatch):
        """Service up returns True when health endpoint responds 200."""
        def _fake_get(url, timeout):
            return SimpleNamespace(status_code=200)

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is True

    def test_service_up_sad(self, monkeypatch):
        """Service up returns False when a RequestException is raised."""
        def _fake_get(url, timeout):
            raise requests.RequestException("Service down")

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is False

    def test_service_up_unexpected_timeout(self, monkeypatch):
        """Service up returns False when a timeout occurs contacting the service."""
        def _fake_get(url, timeout):
            raise requests.Timeout("Timeout occurred")

        monkeypatch.setattr(requests, "get", _fake_get)
        assert _service_up(url=BASE_URL) is False

def test_retriever_attaches_http_handler():
    """The retriever process should attach an HTTPLogHandler to its module logger."""
    logger = logging.getLogger("retriever_service")
    handlers = [h for h in logger.handlers if h.__class__.__name__ == "HTTPLogHandler"]
    assert handlers, "retriever_service must attach HTTPLogHandler"

    h = cast(_HTTPLogHandler, handlers[0])
    if hasattr(h, "_stopped"):
        getattr(h, "_stopped").set()
    if hasattr(h, "_worker"):
        getattr(h, "_worker").join(timeout=1)

    
def test_retrieve_documents_as_string(test_client, monkeypatch):
    """Assert retrieve_documents_as_string returns a non-empty concatenated string via API."""
    class FakeRetriever:
        def invoke(self, query):
            return [
                SimpleNamespace(page_content="Doc A"),
                SimpleNamespace(page_content="Doc B"),
            ]
    
    fake_index = SimpleNamespace(as_retriever=lambda *a, **k: FakeRetriever())
    fake_store = SimpleNamespace(id=1, name="test", index_path="test/path")
    
    monkeypatch.setattr(retriever_module.crud, "get_store", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path: fake_index)
    
    resp = test_client.post(
        "/stores/retrieve_string",
        params={"store_id": 1},
        json={"query": "What are the best Iphones?", "k": 5}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    doc_string = data.get("documents", "")
    assert doc_string is not None and len(doc_string) > 0
    assert isinstance(doc_string, str)
    assert "Doc A" in doc_string
    assert "Doc B" in doc_string

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="Retriever service is not running")
def test_health_endpoint():
    """Integration test: check retriever /health endpoint returns expected OK status."""
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"

def _get_first_store_id() -> int | None:
    """Helper to get the first available store_id from the retriever service."""
    try:
        resp = requests.get(f"{BASE_URL}/stores", timeout=5)
        if resp.status_code == 200:
            stores = resp.json()
            if stores:
                return stores[0]["id"]
    except requests.RequestException:
        pass
    return None

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="Retriever service is not running")
def test_retrieve_documents_string_api():
    """Integration test: POST to retrieve_documents_string and assert non-empty string."""
    store_id = _get_first_store_id()
    assert store_id is not None, "Need at least one store in the retriever for this test"
    resp = requests.post(f"{BASE_URL}/stores/retrieve_string?store_id={store_id}", json=PAYLOAD, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
    assert isinstance(data["documents"], str)
    assert data["documents"].strip() != "", "Retrieved document string should not be empty"
    
