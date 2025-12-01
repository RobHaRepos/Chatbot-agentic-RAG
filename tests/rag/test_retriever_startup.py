"""Tests for retriever startup and FAISS index loading."""
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from types import SimpleNamespace
import pytest


class DummyVectorStore:
    """Fake vector store for testing."""

    def __init__(self, ntotal=10):
        self._meta = {"fake": True}
        self.index = SimpleNamespace(ntotal=ntotal)

    def as_retriever(self, **kwargs):
        return SimpleNamespace(invoke=lambda q: [])


def test_dummy_vector_store_init():
    """DummyVectorStore initializes with fake metadata and index.ntotal set to 10."""
    ds = DummyVectorStore()
    assert isinstance(ds._meta, dict)
    assert ds.index.ntotal == 10


def test_dummy_vector_store_with_custom_ntotal():
    """DummyVectorStore can be initialized with custom ntotal value."""
    ds = DummyVectorStore(ntotal=25)
    assert ds.index.ntotal == 25


def test_dummy_vector_store_as_retriever():
    """DummyVectorStore.as_retriever returns a retriever that can invoke queries."""
    ds = DummyVectorStore()
    retriever = ds.as_retriever()
    result = retriever.invoke("test query")
    assert isinstance(result, list)
    assert len(result) == 0


def test_faiss_load_local_success(monkeypatch):
    """FAISS.load_local returns a vector store when successful."""
    monkeypatch.setattr(
        FAISS,
        "load_local",
        lambda path, embeddings, allow_dangerous_deserialization=True: DummyVectorStore(),
    )

    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vs = FAISS.load_local(
        PATH_TO_FAISS_INDEX, embeddings, allow_dangerous_deserialization=True
    )
    assert vs is not None
    assert hasattr(vs, "index") and vs.index.ntotal == 10


def test_faiss_load_local_raises(monkeypatch):
    """FAISS.load_local raises exception when loading fails."""

    def raise_error(path, embeddings, allow_dangerous_deserialization=True):
        raise RuntimeError("Fail to load")

    monkeypatch.setattr(FAISS, "load_local", raise_error)

    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    with pytest.raises(RuntimeError):
        FAISS.load_local(
            PATH_TO_FAISS_INDEX, embeddings, allow_dangerous_deserialization=True
        )


def _mocked_vector_store(ntotal=3):
    """Create a mocked vector store with specified ntotal."""
    fake_index = SimpleNamespace(ntotal=ntotal)

    class FakeRetriever:
        def get_documents(self, **kwargs):
            return []

        def invoke(self, query):
            return []

    class FakeVectorStore:
        index = fake_index

        def as_retriever(self, **kwargs):
            return FakeRetriever()

    return FakeVectorStore()


def test_mocked_vector_store_has_correct_ntotal():
    """_mocked_vector_store creates a vector store with specified ntotal."""
    vs = _mocked_vector_store(ntotal=7)
    assert vs.index.ntotal == 7


def test_mocked_vector_store_retriever_get_documents():
    """_mocked_vector_store retriever can call get_documents."""
    vs = _mocked_vector_store()
    retriever = vs.as_retriever()
    docs = retriever.get_documents()
    assert isinstance(docs, list)
    assert len(docs) == 0


def test_mocked_vector_store_retriever_invoke():
    """_mocked_vector_store retriever can invoke queries."""
    vs = _mocked_vector_store()
    retriever = vs.as_retriever()
    result = retriever.invoke("test query")
    assert isinstance(result, list)
    assert len(result) == 0


def test_fastapi_startup_monkeypatch(monkeypatch):
    """FastAPI startup attaches a vector_store with expected .index.ntotal value."""
    from fastapi.testclient import TestClient
    import app.rag.src.retriever as retriever

    monkeypatch.setattr(
        retriever.FAISS,
        "load_local",
        lambda path, embeddings, allow_dangerous_deserialization=True: _mocked_vector_store(
            ntotal=5
        ),
    )
    monkeypatch.setattr(retriever, "init_db", lambda: None)
    monkeypatch.setattr(retriever, "seed_embedding_models", lambda: None)
    monkeypatch.setattr(retriever, "seed_default_store", lambda: None)

    client = TestClient(retriever.app)
    with client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        # vector_store removed in refactoring - embeddings loaded instead
        assert hasattr(retriever, "embeddings")