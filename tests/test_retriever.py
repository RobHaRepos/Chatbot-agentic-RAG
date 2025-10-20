from app.rag.retriever import load_faiss_index
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from langchain_huggingface import HuggingFaceEmbeddings

import app.rag.retriever as retriever_module
from app.rag.retriever import SearchRequest

def test_retrieve_documents_as_string():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    retriever_module.vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    req = SearchRequest(query="What are the best Iphones?", k=5)

    docs = retriever_module.retrieve_documents_as_string(req)
    doc_string = docs.get("documents", "")
    print(type(doc_string))
    print(doc_string)
    assert doc_string is not None and len(doc_string) > 0
    assert isinstance(doc_string, str)

def test_retrieve_documents_as_list():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    retriever_module.vector_store = load_faiss_index(PATH_TO_FAISS_INDEX, embeddings)
    req = SearchRequest(query="What are the best Iphones?", k=5)
    docs = retriever_module.retrieve_documents_as_list(req)
    doc_list = docs.documents
    print(type(doc_list))
    print(doc_list)
    assert doc_list is not None and len(doc_list) > 0
    assert isinstance(doc_list, list)