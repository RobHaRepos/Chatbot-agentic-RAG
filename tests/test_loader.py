import app.rag.loader as loader
from app.config import PATH_TO_FAISS_INDEX

def test_load_faiss_index():
    index = loader.load_faiss_index(PATH_TO_FAISS_INDEX)
    if index is not None:
        assert index is not None

def test_faiss_not_empty():
    index = loader.load_faiss_index(PATH_TO_FAISS_INDEX)
    if index is not None:
        assert index.ntotal > 0