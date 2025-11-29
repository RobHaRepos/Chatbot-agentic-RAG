"""Tests for retriever API CRUD endpoints."""
import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import MagicMock
import app.rag.src.retriever as retriever_module


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked dependencies."""

    monkeypatch.setattr(
        retriever_module.FAISS,
        "load_local",
        lambda *a, **k: SimpleNamespace(as_retriever=lambda **x: MagicMock()),
    )
    monkeypatch.setattr(retriever_module, "embeddings", SimpleNamespace(), raising=False)
    monkeypatch.setattr(
        retriever_module,
        "vector_store",
        SimpleNamespace(as_retriever=lambda **k: SimpleNamespace(invoke=lambda q: [])),
        raising=False,
    )

    monkeypatch.setattr(retriever_module, "init_db", lambda: None)
    monkeypatch.setattr(retriever_module, "seed_embedding_models", lambda: None)
    monkeypatch.setattr(retriever_module, "seed_default_store", lambda: None)

    return TestClient(retriever_module.app)


def _make_fake_embedding_model():
    """Create a fake embedding model object."""
    return SimpleNamespace(
        id=1,
        name="all-MiniLM-L6-v2",
        display_name="MiniLM L6 (Fast)",
        dimension=384,
        description="Fast model",
        is_available=True,
    )


def _make_fake_store(store_id=1, name="test-store"):
    """Create a fake vector store object."""
    return SimpleNamespace(
        id=store_id,
        name=name,
        description="Test store",
        document_count=0,
        chunk_count=0,
        is_active=True,
        index_path="data/stores/test",
        embedding_model=_make_fake_embedding_model(),
    )


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint returns 200 OK."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestEmbeddingModelsEndpoint:
    """Tests for /embedding-models endpoint."""

    def test_list_embedding_models(self, client, monkeypatch):
        """GET /embedding-models returns list of models."""
        fake_models = [_make_fake_embedding_model()]
        monkeypatch.setattr(
            retriever_module.crud, "get_embedding_models", lambda db: fake_models
        )

        resp = client.get("/embedding-models")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "all-MiniLM-L6-v2"
        assert data[0]["dimension"] == 384

    def test_list_embedding_models_empty(self, client, monkeypatch):
        """GET /embedding-models returns empty list when no models exist."""
        monkeypatch.setattr(retriever_module.crud, "get_embedding_models", lambda db: [])

        resp = client.get("/embedding-models")

        assert resp.status_code == 200
        assert resp.json() == []


class TestVectorStoresCRUD:
    """Tests for /stores CRUD endpoints."""

    def test_list_stores(self, client, monkeypatch):
        """GET /stores returns list of stores."""
        fake_store = _make_fake_store()
        monkeypatch.setattr(retriever_module.crud, "get_stores", lambda db: [fake_store])

        resp = client.get("/stores")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-store"

    def test_list_stores_empty(self, client, monkeypatch):
        """GET /stores returns empty list when no stores exist."""
        monkeypatch.setattr(retriever_module.crud, "get_stores", lambda db: [])

        resp = client.get("/stores")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_store(self, client, monkeypatch):
        """POST /stores creates a new store."""
        fake_store = _make_fake_store(name="new-store")
        monkeypatch.setattr(
            retriever_module.crud, "create_store", lambda db, s: fake_store
        )

        resp = client.post(
            "/stores",
            json={"name": "new-store", "description": "New", "embedding_model_id": 1},
        )

        assert resp.status_code == 201
        assert resp.json()["name"] == "new-store"

    def test_create_store_validation_error(self, client):
        """POST /stores returns 422 for invalid data."""
        resp = client.post("/stores", json={"name": "", "embedding_model_id": 1})

        assert resp.status_code == 422

    def test_get_store_found(self, client, monkeypatch):
        """GET /stores/{id} returns store when found."""
        fake_store = _make_fake_store()
        monkeypatch.setattr(
            retriever_module.crud, "get_store", lambda db, id: fake_store
        )

        resp = client.get("/stores/1")

        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_store_not_found(self, client, monkeypatch):
        """GET /stores/{id} returns 404 when not found."""
        monkeypatch.setattr(retriever_module.crud, "get_store", lambda db, id: None)

        resp = client.get("/stores/999")

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_update_store_found(self, client, monkeypatch):
        """PUT /stores/{id} updates store."""
        fake_store = _make_fake_store(name="updated-store")
        monkeypatch.setattr(
            retriever_module.crud, "update_store", lambda db, id, u: fake_store
        )

        resp = client.put("/stores/1", json={"name": "updated-store"})

        assert resp.status_code == 200
        assert resp.json()["name"] == "updated-store"

    def test_update_store_not_found(self, client, monkeypatch):
        """PUT /stores/{id} returns 404 when not found."""
        monkeypatch.setattr(retriever_module.crud, "update_store", lambda db, id, u: None)

        resp = client.put("/stores/999", json={"name": "x"})

        assert resp.status_code == 404

    def test_delete_store_success(self, client, monkeypatch):
        """DELETE /stores/{id} returns 204 on success."""
        monkeypatch.setattr(retriever_module.crud, "delete_store", lambda db, id: True)
        retriever_module.loaded_stores.clear()

        resp = client.delete("/stores/1")

        assert resp.status_code == 204

    def test_delete_store_not_found(self, client, monkeypatch):
        """DELETE /stores/{id} returns 404 when not found."""
        monkeypatch.setattr(retriever_module.crud, "delete_store", lambda db, id: False)

        resp = client.delete("/stores/999")

        assert resp.status_code == 404

    def test_delete_store_invalidates_cache(self, client, monkeypatch):
        """DELETE /stores/{id} removes store from loaded_stores cache."""
        retriever_module.loaded_stores[1] = MagicMock(spec=retriever_module.FAISS)
        monkeypatch.setattr(retriever_module.crud, "delete_store", lambda db, id: True)

        client.delete("/stores/1")

        assert 1 not in retriever_module.loaded_stores


class TestRetrievalEndpoints:
    """Tests for retrieval endpoints."""

    def test_retrieve_from_store_success(self, client, monkeypatch):
        """POST /stores/{id}/retrieve returns chunks."""
        fake_store = _make_fake_store()
        monkeypatch.setattr(
            retriever_module.crud, "get_store", lambda db, id: fake_store
        )

        fake_doc = SimpleNamespace(
            page_content="Hello world", metadata={"source": "test"}
        )
        fake_index = SimpleNamespace(
            similarity_search_with_score=lambda q, k: [(fake_doc, 0.5)]
        )
        monkeypatch.setattr(
            retriever_module, "get_store_index", lambda id, path: fake_index
        )

        resp = client.post("/stores/1/retrieve", json={"query": "test", "k": 5})

        assert resp.status_code == 200
        data = resp.json()
        assert data["store_id"] == 1
        assert data["store_name"] == "test-store"
        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["content"] == "Hello world"
        assert data["chunks"][0]["score"] == pytest.approx(0.5)

    def test_retrieve_from_store_not_found(self, client, monkeypatch):
        """POST /stores/{id}/retrieve returns 404 for unknown store."""
        monkeypatch.setattr(retriever_module.crud, "get_store", lambda db, id: None)

        resp = client.post("/stores/999/retrieve", json={"query": "test", "k": 5})

        assert resp.status_code == 404

    def test_retrieve_from_store_multiple_chunks(self, client, monkeypatch):
        """POST /stores/{id}/retrieve returns multiple chunks."""
        fake_store = _make_fake_store()
        monkeypatch.setattr(
            retriever_module.crud, "get_store", lambda db, id: fake_store
        )

        fake_docs = [
            (SimpleNamespace(page_content="Doc 1", metadata={}), 0.1),
            (SimpleNamespace(page_content="Doc 2", metadata={}), 0.3),
            (SimpleNamespace(page_content="Doc 3", metadata={}), 0.5),
        ]
        fake_index = SimpleNamespace(similarity_search_with_score=lambda q, k: fake_docs)
        monkeypatch.setattr(
            retriever_module, "get_store_index", lambda id, path: fake_index
        )

        resp = client.post("/stores/1/retrieve", json={"query": "test", "k": 3})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["chunks"]) == 3

    def test_retrieve_string_success(self, client, monkeypatch):
        """POST /stores/retrieve_string returns concatenated string."""
        fake_store = _make_fake_store()
        monkeypatch.setattr(
            retriever_module.crud, "get_store", lambda db, id: fake_store
        )

        fake_docs = [
            SimpleNamespace(page_content="Doc 1"),
            SimpleNamespace(page_content="Doc 2"),
        ]
        fake_retriever = SimpleNamespace(invoke=lambda q: fake_docs)
        fake_index = SimpleNamespace(as_retriever=lambda **k: fake_retriever)
        monkeypatch.setattr(
            retriever_module, "get_store_index", lambda id, path: fake_index
        )

        resp = client.post(
            "/stores/retrieve_string",
            params={"store_id": 1},
            json={"query": "test", "k": 2},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Doc 1" in data["documents"]
        assert "Doc 2" in data["documents"]

    def test_retrieve_string_store_not_found(self, client, monkeypatch):
        """POST /stores/retrieve_string returns 404 for unknown store."""
        monkeypatch.setattr(retriever_module.crud, "get_store", lambda db, id: None)

        resp = client.post(
            "/stores/retrieve_string",
            params={"store_id": 999},
            json={"query": "test"},
        )

        assert resp.status_code == 404

    def test_retrieve_string_uses_default_k(self, client, monkeypatch):
        """POST /stores/retrieve_string uses DEFAULT_K when k not provided."""
        fake_store = _make_fake_store()
        monkeypatch.setattr(
            retriever_module.crud, "get_store", lambda db, id: fake_store
        )

        captured_k = []

        def fake_as_retriever(**kwargs):
            captured_k.append(kwargs.get("search_kwargs", {}).get("k"))
            return SimpleNamespace(invoke=lambda q: [])

        fake_index = SimpleNamespace(as_retriever=fake_as_retriever)
        monkeypatch.setattr(
            retriever_module, "get_store_index", lambda id, path: fake_index
        )
        monkeypatch.setattr(retriever_module, "DEFAULT_K", 10)

        client.post(
            "/stores/retrieve_string",
            params={"store_id": 1},
            json={"query": "test"},
        )

        assert captured_k[0] == 10
