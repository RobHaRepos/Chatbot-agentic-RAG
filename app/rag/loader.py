from langchain_community.vectorstores import FAISS

def load_faiss_index(Path, embeddings):
    vector_store = FAISS.load_local(Path, embeddings, allow_dangerous_deserialization=True)
    return vector_store