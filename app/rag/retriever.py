from langchain.tools.retriever import create_retriever_tool
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from typing import Optional, List, Any
from app.config import NUMBER_OF_DOCUMENTS_TO_RETRIEVE as k
from app.config import PATH_TO_FAISS_INDEX, MODEL_NAME_EMBEDDING
from fastapi import FastAPI
from contextlib import asynccontextmanager
from langchain_community.vectorstores import FAISS

def load_faiss_index(path: str, embeddings, allow_dangerous_deserialization: bool = True):
    """
    Wrapper so tests that import app.rag.retriever can call load_faiss_index.
    """
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=allow_dangerous_deserialization)

class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = None

class DocumentsResponse(BaseModel):
    documents: List[Any]

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
def retrieve_documents_as_string(req : SearchRequest) -> str:
    kk = req.k or k
    retriever_tool = create_retriever_tool(vector_store.as_retriever(search_type="similarity", search_kwargs={"k": kk}))
    docs = retriever_tool.run(req.query)
    return {"documents": docs}

@app.post("/retrieve_documents_list", response_model=DocumentsResponse)
def retrieve_documents_as_list(req: SearchRequest) -> DocumentsResponse:
    kk = req.k or k
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": kk})
    docs = retriever.invoke(req.query)
    return DocumentsResponse(documents=docs)

@app.get("/health")
def health_check():
    return {"status": "ok"}