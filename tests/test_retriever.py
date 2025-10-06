from app.rag.retriever import retrieve_documents, create_retriever_tool_from_vectorstore
from app.rag.loader import load_faiss_index
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings

def test_retrieve_documents():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    retriever = create_retriever_tool_from_vectorstore(vector_store)
    query = "What are the best Iphones?"
    docs = retrieve_documents(query, retriever)
    print(docs)
    assert docs is not None and len(docs) > 0 