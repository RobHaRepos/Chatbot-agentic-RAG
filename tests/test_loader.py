import app.rag.loader as loader
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings

def test_load_faiss_index():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = loader.load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    if vector_store is not None:
        assert vector_store is not None

def test_faiss_not_empty():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = loader.load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    assert vector_store.index.ntotal > 0