from app.rag.retriever import retrieve_documents_as_list, create_retriever_from_vectorstore
from app.rag.retriever import retrieve_documents_as_string, create_retriever_tool_from_vectorstore
from app.rag.loader import load_faiss_index
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings

def test_retrieve_documents_as_string():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    retriever = create_retriever_tool_from_vectorstore(vector_store)
    query = "What are the best Iphones?"
    docs = retrieve_documents_as_string(query, retriever)
    print(type(docs))
    print(docs)
    assert docs is not None and len(docs) > 0
    assert isinstance(docs, str)
    
def test_retrieve_documents_as_list():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    retriever = create_retriever_from_vectorstore(vector_store)
    query = "What are the best Iphones?"
    docs = retrieve_documents_as_list(query, retriever)
    print(type(docs))
    print(docs)
    assert docs is not None and len(docs) > 0  
    assert isinstance(docs, list) 