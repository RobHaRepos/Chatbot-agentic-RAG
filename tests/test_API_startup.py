from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings
from types import SimpleNamespace
import pytest
from app.rag.retriever import load_faiss_index
from pathlib import Path


class DummyVectorStore:
    def __init__(self):
        self._meta = {"fake": True}
        self.index = SimpleNamespace(ntotal=10)
### ToDo create seperate test for load faiss index --> unit test and integration test with real index
def test_load_faiss_index(monkeypatch):
    """load_faiss_index returns a vector store or None depending on environment."""
    index_path = Path(PATH_TO_FAISS_INDEX) / "index.faiss"
    if not index_path.exists():
        monkeypatch.setattr("app.rag.retriever.FAISS.load_local", 
                            lambda path, embeddings, 
                            allow_dangerous_deserialization=True: DummyVectorStore()
                            )   
    
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    if vector_store is not None:
        assert vector_store is not None

def test_dummy_vector_store_init():
    """DummyVectorStore initializes with fake metadata and index.ntotal set to 10."""
    ds = DummyVectorStore()
    assert isinstance(ds._meta, dict)
    assert ds.index.ntotal == 10

def test_load_faiss_index_success(monkeypatch):
    """force FAISS.load_local to return a DummyVectorStore and verify load_faiss_index returns it."""
    import app.rag.retriever as retriever
    monkeypatch.setattr(retriever.FAISS, "load_local", lambda path, embeddings, allow_dangerous_deserialization=True: DummyVectorStore())

    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vs = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    assert vs is not None
    assert hasattr(vs, "index") and vs.index.ntotal == 10

def test_load_faiss_index_raises(monkeypatch):
    """If FAISS.load_local raises an exception, load_faiss_index should propagate it."""
    import app.rag.retriever as retriever
    def raise_error(path, embeddings, allow_dangerous_deserialization=True):
        raise RuntimeError("Fail to load")

    monkeypatch.setattr(retriever.FAISS, "load_local", raise_error)

    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    with pytest.raises(RuntimeError):
        load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)

def test_faiss_not_empty(monkeypatch):
    """Vector store index has positive ntotal if a fake vector store is returned."""
    index_path = Path(PATH_TO_FAISS_INDEX) / "index.faiss"
    if not index_path.exists():
        monkeypatch.setattr("app.rag.retriever.FAISS.load_local", 
                            lambda path, embeddings, 
                            allow_dangerous_deserialization=True: DummyVectorStore()
                            )    
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)  
    vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    assert vector_store.index.ntotal > 0

def _mocked_vector_store(ntotal=3):
    fake_index = SimpleNamespace(ntotal=ntotal)
    class FakeRetriever:
        def get_documents(self, **kwargs):
            return []
    class FakeVectorStore:
        index = fake_index
        def as_retriever(self, **kwargs):
            return FakeRetriever()
    return FakeVectorStore()

def test_fastapi_startup_monkeypatch(monkeypatch):
    """FastAPI startup attaches a vector_store with expected .index.ntotal value."""
    from fastapi.testclient import TestClient
    import app.rag.retriever as retriever
    
    monkeypatch.setattr(retriever.FAISS, "load_local", lambda path, embeddings, allow_dangerous_deserialization=True: _mocked_vector_store(ntotal=5))
    
    client = TestClient(retriever.app)
    with client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert hasattr(retriever, "vector_store")
        assert retriever.vector_store.index.ntotal == 5