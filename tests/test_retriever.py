from app.rag.retriever import load_faiss_index
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings

import app.rag.retriever as retriever_module
from app.rag.retriever import SearchRequest

def test_retrieve_documents_as_string():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    retriever_module.vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    retriever = retriever_module.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    req = SearchRequest(query="What are the best Iphones?", k=5)

    docs = retriever_module.retrieve_documents_as_string(req, retriever)
    print(type(docs))
    print(docs)
    assert docs is not None and len(docs) > 0
    assert isinstance(docs, str)
    
def test_retrieve_documents_as_list():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    retriever_module.vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    retriever = retriever_module.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    req = SearchRequest(query="What are the best Iphones?", k=5)
    docs = retriever_module.retrieve_documents_as_list(req, retriever)
    print(type(docs))
    print(docs)
    assert docs is not None and len(docs) > 0  
    assert isinstance(docs, list) 