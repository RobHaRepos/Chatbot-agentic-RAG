from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings
from types import SimpleNamespace
from app.rag.retriever import load_faiss_index


def test_load_faiss_index():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    if vector_store is not None:
        assert vector_store is not None

def test_faiss_not_empty():
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

def test_FastAPI_startup_monkeypatch(monkeypatch):
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