import logging
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from typing import Optional, List, Any
from fastapi import FastAPI
from contextlib import asynccontextmanager
from langchain_community.vectorstores import FAISS

import os
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# environment-driven configurations
PATH_TO_FAISS_INDEX = os.environ.get("PATH_TO_FAISS_INDEX", str(Path(__file__).resolve().parent.parent.parent / "faiss_Hugging_index"))
MODEL_NAME_EMBEDDING = os.environ.get("MODEL_NAME_EMBEDDING", "")
NUMBER_OF_DOCUMENTS_TO_RETRIEVE = int(os.environ.get("NUMBER_OF_DOCUMENTS_TO_RETRIEVE", 5))

class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = None

class DocumentsResponse(BaseModel):
    documents: List[Any]

def load_faiss_index(path: str, embeddings, allow_dangerous_deserialization: bool = True):
    """
    Wrapper so tests that import app.rag.retriever can call load_faiss_index.
    """
    logger.info("load_faiss_index: loading FAISS index from path=%s", path)
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=allow_dangerous_deserialization)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store, embeddings
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)
    vector_store = FAISS.load_local(PATH_TO_FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)
    try:
        yield
    finally:
        pass
    
app = FastAPI(lifespan=lifespan)

@app.post("/retrieve_documents_string")
def retrieve_documents_as_string(req : SearchRequest) -> dict:
    kk = req.k or NUMBER_OF_DOCUMENTS_TO_RETRIEVE
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": kk})
    docs = retriever.invoke(req.query)
    
    complete_doc_String = ""
    for doc in docs:
        complete_doc_String += doc.page_content + "\n\n"
    logger.info("retrieve_documents_as_string: complete_doc_String=%s", complete_doc_String)
    return {"documents": complete_doc_String}

@app.post("/retrieve_documents_list", response_model=DocumentsResponse)
def retrieve_documents_as_list(req: SearchRequest) -> DocumentsResponse:
    kk = req.k or NUMBER_OF_DOCUMENTS_TO_RETRIEVE
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": kk})
    docs = retriever.invoke(req.query)
    logger.info("retrieve_documents_as_list: retrieved %d documents", len(docs))
    return DocumentsResponse(documents=docs)

@app.get("/health")
def health_check():
    return {"status": "ok"}