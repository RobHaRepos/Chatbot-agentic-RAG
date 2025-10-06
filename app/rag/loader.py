from langchain_community.vectorstores import FAISS
from app.config import NUMBER_OF_DOCUMENTS_TO_RETRIEVE as k

def load_faiss_index(Path, embeddings):
    vector_store = FAISS.load_local(Path, embeddings, allow_dangerous_deserialization=True)
    return vector_store