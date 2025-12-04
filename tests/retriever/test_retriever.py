import asyncio
import logging
import requests
from contextlib import contextmanager
from io import BytesIO
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import langchain_huggingface
import pytest
from fastapi.testclient import TestClient

import app.retriever.src.retriever as retriever_module
from app.logger_service.handlers import HTTPLogHandler as _HTTPLogHandler
from app.retriever.src import crud
from app.retriever.src.database import get_db

BASE_URL = "http://localhost:8001"
PAYLOAD = {
    "query": "What are the newest Iphones?",
    "k": 10
}


@contextmanager
def override_db(fake_db_instance=None):
    """Context manager to override FastAPI get_db dependency."""
    class FakeDB:
        pass
    
    db_instance = fake_db_instance if fake_db_instance is not None else FakeDB()
    
    def override_get_db():
        yield db_instance
    
    retriever_module.app.dependency_overrides[get_db] = override_get_db
    try:
        yield db_instance
    finally:
        retriever_module.app.dependency_overrides.clear()


class FakeSession:
    """Reusable fake session class that mocks SQLAlchemy session methods."""
    def commit(self):
        """Mock commit - no DB operations needed in test."""
    def refresh(self, obj):
        """Mock refresh - no DB operations needed in test."""
    def rollback(self):
        """Mock rollback - no DB operations needed in test."""


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
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    
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

@pytest.mark.integration
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


def test_service_up_returns_false_when_not_reachable(monkeypatch):
    """_service_up returns False when service is not reachable."""
    def mock_get_raises(*args, **kwargs):
        raise requests.RequestException("Connection failed")
    
    monkeypatch.setattr(requests, "get", mock_get_raises)
    assert _service_up("https://fake-url") is False


def test_service_up_returns_false_on_non_200(monkeypatch):
    """_service_up returns False when status code is not 200."""
    mock_response = SimpleNamespace(status_code=500)
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)
    assert _service_up("https://fake-url") is False


def test_get_first_store_id_returns_none_on_exception(monkeypatch):
    """_get_first_store_id returns None when request raises exception."""
    def mock_get_raises(*args, **kwargs):
        raise requests.RequestException("Connection failed")
    
    monkeypatch.setattr(requests, "get", mock_get_raises)
    assert _get_first_store_id() is None


def test_get_first_store_id_returns_none_on_non_200(monkeypatch):
    """_get_first_store_id returns None when status code is not 200."""
    mock_response = SimpleNamespace(status_code=500)
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)
    assert _get_first_store_id() is None


def test_get_first_store_id_returns_none_when_no_stores(monkeypatch):
    """_get_first_store_id returns None when stores list is empty."""
    mock_response = SimpleNamespace(status_code=200, json=lambda: [])
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)
    assert _get_first_store_id() is None


# ====== Additional tests to increase coverage ======

def test_retrieve_documents_as_string_no_index(test_client, monkeypatch):
    """Test retrieve_documents_as_string when index is None (no documents yet)."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="test/path")
    
    monkeypatch.setattr(retriever_module.crud, "get_store", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: None)
    
    resp = test_client.post(
        "/stores/retrieve_string",
        params={"store_id": 1},
        json={"query": "What are the best Iphones?", "k": 5}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["documents"] == ""


def test_list_embedding_models(test_client, monkeypatch):
    """Test listing all embedding models."""
    fake_models = [
        SimpleNamespace(id=1, name="model1", display_name="Model 1", dimension=384, description="desc1", is_available=True),
        SimpleNamespace(id=2, name="model2", display_name="Model 2", dimension=768, description="desc2", is_available=True),
    ]
    monkeypatch.setattr(retriever_module.crud, "get_embedding_models", lambda db: fake_models)
    
    resp = test_client.get("/embedding-models")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_stores(test_client, monkeypatch):
    """Test listing all vector stores."""
    fake_embedding_model = SimpleNamespace(
        id=1, name="model1", display_name="Model 1", 
        dimension=384, description="desc1", is_available=True
    )
    fake_stores = [
        SimpleNamespace(id=1, name="store1", description="desc1", embedding_model=fake_embedding_model, 
                       document_count=0, chunk_count=0, is_active=True),
        SimpleNamespace(id=2, name="store2", description="desc2", embedding_model=fake_embedding_model,
                       document_count=0, chunk_count=0, is_active=True),
    ]
    monkeypatch.setattr(retriever_module.crud, "get_stores", lambda db: fake_stores)
    
    resp = test_client.get("/stores")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_create_store(test_client, monkeypatch):
    """Test creating a new vector store."""
    fake_embedding_model = SimpleNamespace(
        id=1, name="model1", display_name="Model 1",
        dimension=384, description="desc1", is_available=True
    )
    fake_store = SimpleNamespace(
        id=1, name="new_store", description="desc", embedding_model=fake_embedding_model,
        document_count=0, chunk_count=0, is_active=True, index_path="fake/path"
    )
    monkeypatch.setattr(retriever_module.crud, "create_store", lambda db, store: fake_store)
    
    resp = test_client.post(
        "/stores",
        json={"name": "new_store", "embedding_model_id": 1}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "new_store"


def test_get_store_endpoint(test_client, monkeypatch):
    """Test getting a specific store by ID."""
    fake_embedding_model = SimpleNamespace(
        id=1, name="model1", display_name="Model 1",
        dimension=384, description="desc1", is_available=True
    )
    fake_store = SimpleNamespace(
        id=1, name="test_store", description="desc", embedding_model=fake_embedding_model,
        document_count=0, chunk_count=0, is_active=True
    )
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    
    resp = test_client.get("/stores/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1


def test_update_store_endpoint(test_client, monkeypatch):
    """Test updating a store successfully."""
    fake_embedding_model = SimpleNamespace(
        id=1, name="model1", display_name="Model 1",
        dimension=384, description="desc1", is_available=True
    )
    fake_store = SimpleNamespace(
        id=1, name="updated_store", description="desc", embedding_model=fake_embedding_model,
        document_count=0, chunk_count=0, is_active=True
    )
    monkeypatch.setattr(retriever_module.crud, "update_store", lambda db, id, update: fake_store)
    
    resp = test_client.patch("/stores/1", json={"name": "updated_store"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "updated_store"


def test_update_store_endpoint_not_found(test_client, monkeypatch):
    """Test updating a store that doesn't exist."""
    monkeypatch.setattr(retriever_module.crud, "update_store", lambda db, id, update: None)
    
    resp = test_client.patch("/stores/999", json={"name": "nonexistent"})
    assert resp.status_code == 404


def test_delete_store_endpoint(test_client, monkeypatch):
    """Test deleting a store successfully."""
    monkeypatch.setattr(retriever_module, "invalidate_store_index", lambda id: None)
    monkeypatch.setattr(retriever_module.crud, "delete_store", lambda db, id: True)
    
    resp = test_client.delete("/stores/1")
    assert resp.status_code == 204


def test_delete_store_endpoint_not_found(test_client, monkeypatch):
    """Test deleting a store that doesn't exist."""
    monkeypatch.setattr(retriever_module, "invalidate_store_index", lambda id: None)
    monkeypatch.setattr(retriever_module.crud, "delete_store", lambda db, id: False)
    
    resp = test_client.delete("/stores/999")
    assert resp.status_code == 404


def test_retrieve_from_store(test_client, monkeypatch):
    """Test retrieving documents from a store."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        page_content="Test content",
        metadata={"source": "test.txt"}
    )
    fake_index = SimpleNamespace(
        similarity_search_with_score=lambda query, k: [(fake_doc, 0.95)]
    )
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    
    resp = test_client.post("/stores/1/retrieve", json={"query": "test", "k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["store_id"] == 1
    assert len(data["chunks"]) == 1


def test_retrieve_from_store_no_index(test_client, monkeypatch):
    """Test retrieving from a store with no index yet."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: None)
    
    resp = test_client.post("/stores/1/retrieve", json={"query": "test", "k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["store_id"] == 1
    assert len(data["chunks"]) == 0


def test_list_documents(test_client, monkeypatch):
    """Test listing documents in a store."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_docs = [
        SimpleNamespace(id=1, filename="doc1.txt", file_type="text/plain", file_size=100, chunk_count=2),
        SimpleNamespace(id=2, filename="doc2.txt", file_type="text/plain", file_size=200, chunk_count=3),
    ]
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_documents", lambda db, store_id: fake_docs)
    
    resp = test_client.get("/stores/1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_get_document(test_client, monkeypatch):
    """Test getting a single document with full content."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="test.txt", file_type="text/plain", 
        file_size=100, chunk_count=2, store_id=1
    )
    
    # Create fake index with document chunks
    fake_chunk1 = SimpleNamespace(
        page_content="Chunk 1 content",
        metadata={retriever_module.METADATA_DOCUMENT_ID: 1, retriever_module.METADATA_CHUNK_INDEX: 0}
    )
    fake_chunk2 = SimpleNamespace(
        page_content="Chunk 2 content",
        metadata={retriever_module.METADATA_DOCUMENT_ID: 1, retriever_module.METADATA_CHUNK_INDEX: 1}
    )
    fake_index = SimpleNamespace(
        docstore=SimpleNamespace(
            _dict={"id1": fake_chunk1, "id2": fake_chunk2}
        )
    )
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    
    resp = test_client.get("/stores/1/documents/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["filename"] == "test.txt"
    assert "Chunk 1 content" in data["content"]
    assert "Chunk 2 content" in data["content"]


def test_get_document_no_index(test_client, monkeypatch):
    """Test getting a document when there's no index yet."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="test.txt", file_type="text/plain",
        file_size=100, chunk_count=0, store_id=1
    )
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: None)
    
    resp = test_client.get("/stores/1/documents/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk_count"] == 0
    assert data["content"] == ""


def test_delete_document_with_remaining_chunks(test_client, monkeypatch):
    """Test deleting a document when other chunks remain in the index."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="test.txt", file_type="text/plain",
        file_size=100, chunk_count=2, store_id=1
    )
    fake_index = SimpleNamespace()
    fake_new_index = SimpleNamespace()
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    monkeypatch.setattr(
        retriever_module, "filter_and_collect_chunks",
        lambda index, filter_fn: (["chunk1", "chunk2"], [{"meta": "data"}])
    )
    monkeypatch.setattr(retriever_module.FAISS, "from_texts", lambda texts, emb, metadatas: fake_new_index)
    monkeypatch.setattr(retriever_module, "save_and_invalidate_index", lambda index, path, id: None)
    monkeypatch.setattr(retriever_module.crud, "delete_document", lambda db, id: None)
    monkeypatch.setattr(retriever_module.crud, "update_store_stats", lambda db, store_id: None)
    
    resp = test_client.delete("/stores/1/documents/1")
    assert resp.status_code == 204


def test_update_document_with_content(test_client, monkeypatch):
    """Test updating document content - tests lines 240-276."""
    
    # Setup fake objects
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="old.txt", file_type="text/plain",
        file_size=50, chunk_count=2, store_id=1
    )
    fake_index = SimpleNamespace()
    fake_new_index = SimpleNamespace()
    
    # Mock all dependencies
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    monkeypatch.setattr(
        retriever_module, "rebuild_index_with_new_content",
        lambda index, doc_id, content, filename, emb: (fake_new_index, 5)
    )
    monkeypatch.setattr(retriever_module, "save_and_invalidate_index", lambda index, path, id: None)
    monkeypatch.setattr(retriever_module.crud, "update_store_stats", lambda db, store_id: None)
    
    with override_db(FakeSession()):
        resp = test_client.patch(
            "/stores/1/documents/1",
            json={"content": "New content", "filename": "new.txt"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "new.txt"
        assert data["chunk_count"] == 5
        assert "file_size" in data
        
        assert fake_doc.filename == "new.txt"
        assert fake_doc.chunk_count == 5


def test_update_document_filename_only(test_client, monkeypatch):
    """Test updating only filename - tests lines 265-271."""
    
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="old.txt", file_type="text/plain",
        file_size=50, chunk_count=2, store_id=1
    )
    fake_index = SimpleNamespace()
    fake_new_index = SimpleNamespace()
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    monkeypatch.setattr(
        retriever_module, "update_index_filenames",
        lambda index, doc_id, filename, emb: fake_new_index
    )
    monkeypatch.setattr(retriever_module, "save_and_invalidate_index", lambda index, path, id: None)
    monkeypatch.setattr(retriever_module.crud, "update_store_stats", lambda db, store_id: None)
    
    with override_db(FakeSession()):
        resp = test_client.patch(
            "/stores/1/documents/1",
            json={"filename": "renamed.txt"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "renamed.txt"
        assert fake_doc.filename == "renamed.txt"


def test_upload_document_creates_index(test_client, monkeypatch):
    """Test uploading document creates new index - tests lines 338-342."""
    
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="uploaded.txt", file_type="text/plain",
        file_size=100, chunk_count=3
    )
    fake_new_index = SimpleNamespace(
        add_texts=lambda texts, metadatas: None
    )
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: None)  # No existing index
    monkeypatch.setattr(retriever_module.RecursiveCharacterTextSplitter, "__init__", lambda self, **kwargs: None)
    monkeypatch.setattr(retriever_module, "validate_upload_file", lambda file: None)
    
    # Use AsyncMock for async function
    async_mock = AsyncMock(return_value=(b"test content", "test content"))
    monkeypatch.setattr(retriever_module, "read_and_decode_file", async_mock)
    
    monkeypatch.setattr(
        retriever_module, "process_file_into_chunks",
        lambda file, text, content, store_id, splitter, db: (
            ["chunk1", "chunk2"], [{"doc_id": 1}, {"doc_id": 1}], fake_doc
        )
    )
    monkeypatch.setattr(retriever_module.FAISS, "from_texts", lambda texts, emb, metadatas: fake_new_index)
    monkeypatch.setattr(retriever_module, "save_and_invalidate_index", lambda index, path, id: None)
    monkeypatch.setattr(retriever_module.crud, "update_store_stats", lambda db, store_id: None)
    
    with override_db(FakeSession()):
        file_content = b"Test file content"
        files = {"files": ("test.txt", BytesIO(file_content), "text/plain")}
        
        resp = test_client.post("/stores/1/upload", files=files)
        
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["filename"] == "uploaded.txt"


def test_upload_document_adds_to_existing_index(test_client, monkeypatch):
    """Test uploading document adds to existing index - tests lines 340-341."""
    
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=2, filename="second.txt", file_type="text/plain",
        file_size=80, chunk_count=2
    )
    
    # Existing index with add_texts method
    texts_added = []
    def track_add_texts(texts, metadatas):
        texts_added.extend(texts)
    
    fake_existing_index = SimpleNamespace(
        add_texts=track_add_texts
    )
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_existing_index)
    monkeypatch.setattr(retriever_module.RecursiveCharacterTextSplitter, "__init__", lambda self, **kwargs: None)
    monkeypatch.setattr(retriever_module, "validate_upload_file", lambda file: None)
    
    # Use AsyncMock for async function
    async_mock = AsyncMock(return_value=(b"more content", "more content"))
    monkeypatch.setattr(retriever_module, "read_and_decode_file", async_mock)
    
    monkeypatch.setattr(
        retriever_module, "process_file_into_chunks",
        lambda file, text, content, store_id, splitter, db: (
            ["new_chunk"], [{"doc_id": 2}], fake_doc
        )
    )
    monkeypatch.setattr(retriever_module, "save_and_invalidate_index", lambda index, path, id: None)
    monkeypatch.setattr(retriever_module.crud, "update_store_stats", lambda db, store_id: None)
    
    with override_db(FakeSession()):
        file_content = b"Second file"
        files = {"files": ("second.txt", BytesIO(file_content), "text/plain")}
        
        resp = test_client.post("/stores/1/upload", files=files)
        
        assert resp.status_code == 200
        assert len(texts_added) > 0
        assert "new_chunk" in texts_added


def test_delete_document_no_remaining_chunks(test_client, monkeypatch):
    """Test deleting the last document in a store."""
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(
        id=1, filename="test.txt", file_type="text/plain",
        file_size=100, chunk_count=2, store_id=1
    )
    fake_index = SimpleNamespace()
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    monkeypatch.setattr(
        retriever_module, "filter_and_collect_chunks",
        lambda index, filter_fn: ([], [])
    )
    monkeypatch.setattr(retriever_module, "remove_index_files", lambda path: None)
    monkeypatch.setattr(retriever_module, "invalidate_store_index", lambda id: None)
    monkeypatch.setattr(retriever_module.crud, "delete_document", lambda db, id: None)
    monkeypatch.setattr(retriever_module.crud, "update_store_stats", lambda db, store_id: None)
    
    resp = test_client.delete("/stores/1/documents/1")
    assert resp.status_code == 204


def test_startup_event(monkeypatch):
    """Test the startup lifespan event - tests lines 62-73, 79."""
    
    init_calls = []
    
    monkeypatch.setattr(retriever_module, "init_db", lambda: init_calls.append("init_db"))
    monkeypatch.setattr(retriever_module, "seed_embedding_models", lambda: init_calls.append("seed_embedding_models"))
    monkeypatch.setattr(retriever_module, "seed_default_store", lambda: init_calls.append("seed_default_store"))
    monkeypatch.setattr(retriever_module, "seed_phone_store_templates", lambda: init_calls.append("seed_phone_store_templates"))
    
    lifespan_cm = retriever_module.lifespan(retriever_module.app)
    
    async def test_lifespan():
        async with lifespan_cm:
            assert "init_db" in init_calls
            assert "seed_embedding_models" in init_calls
            assert "seed_default_store" in init_calls
            assert "seed_phone_store_templates" in init_calls
    
    asyncio.run(test_lifespan())


def test_get_document_empty_chunks(monkeypatch):
    """Test get_document when no chunks are found - tests line 220."""
    
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    fake_doc = SimpleNamespace(id=1, filename="test.txt", file_type="text/plain", file_size=100, chunk_count=0, store_id=1)
    
    fake_dict = {}
    fake_docstore = SimpleNamespace(_dict=fake_dict)
    fake_index = SimpleNamespace(docstore=fake_docstore)
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module.crud, "get_document", lambda db, id: fake_doc)
    monkeypatch.setattr(retriever_module, "validate_document_ownership", lambda doc, doc_id, store_id: None)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: fake_index)
    
    test_client = TestClient(retriever_module.app)
    resp = test_client.get("/stores/1/documents/1")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["content"] == ""


def test_upload_document_with_exception(monkeypatch):
    """Test upload_document exception handling - tests lines 348-353."""
    
    fake_store = SimpleNamespace(id=1, name="test", index_path="path")
    
    monkeypatch.setattr(retriever_module, "get_store_or_404", lambda db, id: fake_store)
    monkeypatch.setattr(retriever_module, "get_store_index", lambda id, path, emb: None)
    monkeypatch.setattr(retriever_module.RecursiveCharacterTextSplitter, "__init__", lambda self, **kwargs: None)
    monkeypatch.setattr(retriever_module, "validate_upload_file", lambda file: None)
    
    async_mock = AsyncMock(return_value=(b"test content", "test content"))
    monkeypatch.setattr(retriever_module, "read_and_decode_file", async_mock)
    
    def failing_process(*args, **kwargs):
        raise ValueError("Simulated processing error")
    
    monkeypatch.setattr(retriever_module, "process_file_into_chunks", failing_process)
    monkeypatch.setattr(retriever_module, "invalidate_store_index", lambda id: None)
    
    # Custom session with tracked rollback for this test
    rollback_called = []
    class TrackedSession(FakeSession):
        def rollback(self):
            rollback_called.append(True)
    
    with override_db(TrackedSession()):
        file_content = b"Test file"
        files = {"files": ("test.txt", BytesIO(file_content), "text/plain")}
        
        test_client = TestClient(retriever_module.app)
        
        try:
            resp = test_client.post("/stores/1/upload", files=files)
            assert resp.status_code == 500 or "error" in resp.text.lower()
        except Exception:
            pass 
        
        assert len(rollback_called) > 0


# ======= Template Endpoint Tests =======
class TestListTemplates:
    """Tests for GET /templates endpoint."""

    def test_list_templates_all(self, test_client):
        """List all templates without filters."""
        fake_templates = [
            SimpleNamespace(
                id=1, name="Template 1", template_type="retrieve_or_respond",
                store_id=1, messages=[{"role": "system", "content": "Test"}], is_active=True
            ),
            SimpleNamespace(
                id=2, name="Template 2", template_type="generate_answer",
                store_id=1, messages=[{"role": "user", "content": "Hi"}], is_active=True
            )
        ]

        class FakeQuery:
            def filter(self, *args):
                return self
            def all(self):
                return fake_templates

        class QueryableDB:
            def query(self, model):
                return FakeQuery()

        with override_db(QueryableDB()):
            resp = test_client.get("/templates")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            assert data[0]["name"] == "Template 1"

    def test_list_templates_by_store_id(self, test_client, monkeypatch):
        """List templates filtered by store_id."""
        fake_templates = [
            SimpleNamespace(
                id=1, name="Store Template", template_type="retrieve_or_respond",
                store_id=5, messages=[{"role": "system", "content": "Test"}], is_active=True
            )
        ]
        monkeypatch.setattr(crud, "get_templates_by_store", lambda db, store_id, t_type: fake_templates)

        with override_db():
            resp = test_client.get("/templates?store_id=5")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["store_id"] == 5

    def test_list_templates_by_type(self, test_client):
        """List templates filtered by type."""
        fake_templates = [
            SimpleNamespace(
                id=1, name="RAG Template", template_type="generate_answer",
                store_id=1, messages=[{"role": "system", "content": "Test"}], is_active=True
            )
        ]

        class FakeQuery:
            def filter(self, *args):
                return self
            def all(self):
                return fake_templates

        class QueryableDB:
            def query(self, model):
                return FakeQuery()

        with override_db(QueryableDB()):
            resp = test_client.get("/templates?template_type=generate_answer")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["template_type"] == "generate_answer"


class TestCreateTemplate:
    """Tests for POST /templates endpoint."""

    def test_create_template_success(self, test_client, monkeypatch):
        """Successfully create a template."""
        created_template = SimpleNamespace(
            id=1, name="New Template", template_type="retrieve_or_respond",
            store_id=1, messages=[{"role": "system", "content": "Test"}], is_active=True
        )
        monkeypatch.setattr(crud, "create_template", lambda db, template: created_template)

        with override_db():
            resp = test_client.post("/templates", json={
                "name": "New Template",
                "template_type": "retrieve_or_respond",
                "store_id": 1,
                "messages": [{"role": "system", "content": "Test"}]
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["name"] == "New Template"
            assert data["id"] == 1

    def test_create_template_invalid_store(self, test_client, monkeypatch):
        """Create template with invalid store returns 400."""
        def raise_value_error(*args, **kwargs):
            raise ValueError("Store not found")
        monkeypatch.setattr(crud, "create_template", raise_value_error)

        with override_db():
            resp = test_client.post("/templates", json={
                "name": "New Template",
                "template_type": "retrieve_or_respond",
                "store_id": 999,
                "messages": [{"role": "system", "content": "Test"}]
            })
            assert resp.status_code == 400
            assert "Store not found" in resp.json()["detail"]


class TestGetTemplate:
    """Tests for GET /templates/{template_id} endpoint."""

    def test_get_template_success(self, test_client, monkeypatch):
        """Successfully get a template by ID."""
        template = SimpleNamespace(
            id=1, name="Template", template_type="retrieve_or_respond",
            store_id=1, messages=[{"role": "system", "content": "Test"}], is_active=True
        )
        monkeypatch.setattr(crud, "get_template", lambda db, template_id: template)

        with override_db():
            resp = test_client.get("/templates/1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == 1
            assert data["name"] == "Template"

    def test_get_template_not_found(self, test_client, monkeypatch):
        """Get non-existent template returns 404."""
        monkeypatch.setattr(crud, "get_template", lambda db, template_id: None)

        with override_db():
            resp = test_client.get("/templates/999")
            assert resp.status_code == 404


class TestUpdateTemplate:
    """Tests for PATCH /templates/{template_id} endpoint."""

    def test_update_template_success(self, test_client, monkeypatch):
        """Successfully update a template."""
        updated_template = SimpleNamespace(
            id=1, name="Updated Template", template_type="retrieve_or_respond",
            store_id=1, messages=[{"role": "system", "content": "Updated"}], is_active=True
        )
        monkeypatch.setattr(crud, "update_template", lambda db, template_id, update: updated_template)

        with override_db():
            resp = test_client.patch("/templates/1", json={"name": "Updated Template"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Updated Template"

    def test_update_template_not_found(self, test_client, monkeypatch):
        """Update non-existent template returns 404."""
        monkeypatch.setattr(crud, "update_template", lambda db, template_id, update: None)

        with override_db():
            resp = test_client.patch("/templates/999", json={"name": "Updated"})
            assert resp.status_code == 404


class TestDeleteTemplate:
    """Tests for DELETE /templates/{template_id} endpoint."""

    def test_delete_template_success(self, test_client, monkeypatch):
        """Successfully delete a template."""
        monkeypatch.setattr(crud, "delete_template", lambda db, template_id: True)

        with override_db():
            resp = test_client.delete("/templates/1")
            assert resp.status_code == 204

    def test_delete_template_not_found(self, test_client, monkeypatch):
        """Delete non-existent template returns 404."""
        monkeypatch.setattr(crud, "delete_template", lambda db, template_id: False)

        with override_db():
            resp = test_client.delete("/templates/999")
            assert resp.status_code == 404