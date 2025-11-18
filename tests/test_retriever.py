from types import SimpleNamespace
import requests
import pytest
import logging
import app.rag.retriever as retriever_module
from app.rag.retriever import SearchRequest

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
            # No-op stub initializer.
            # The real `HuggingFaceEmbeddings` performs expensive model loading
            # and external I/O which we must avoid in unit tests. This empty
            # initializer lets tests substitute a lightweight stand-in without
            # triggering the external dependencies.
            pass
    monkeypatch.setattr(langchain_huggingface, "HuggingFaceEmbeddings", CheapEmb)

    return fake_store

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

    
def test_retrieve_documents_as_string(fake_vector_store):
    """Assert retrieve_documents_as_string returns a non-empty concatenated string."""
    req = SearchRequest(query="What are the best Iphones?", k=5)

    docs = retriever_module.retrieve_documents_as_string(req)
    doc_string = docs.get("documents", "")
    print(type(doc_string))
    print(doc_string)
    assert doc_string is not None and len(doc_string) > 0
    assert isinstance(doc_string, str)
    assert "Doc A" in doc_string
    assert "Doc B" in doc_string

def test_retrieve_documents_as_list(fake_vector_store):
    """Assert retrieve_documents_as_list returns a non-empty list of documents."""
    req = SearchRequest(query="What are the best Iphones?", k=5)
    docs = retriever_module.retrieve_documents_as_list(req)
    doc_list = docs.documents
    print(type(doc_list))
    print(doc_list)
    assert doc_list is not None and len(doc_list) > 0
    assert isinstance(doc_list, list)
    assert any("Doc A" == doc.page_content for doc in doc_list)
    assert any("Doc B" == doc.page_content for doc in doc_list)

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="Retriever service is not running")
def test_health_endpoint():
    """Integration test: check retriever /health endpoint returns expected OK status."""
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"

@pytest.mark.skipif(not _service_up(url=BASE_URL), reason="Retriever service is not running")
def test_retrieve_documents_string_api():
    """Integration test: POST to retrieve_documents_string and assert non-empty string."""
    resp = requests.post(f"{BASE_URL}/retrieve_documents_string", json=PAYLOAD, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
    assert isinstance(data["documents"], str)
    assert data["documents"].strip() != "", "Retrieved document string should not be empty"
    
