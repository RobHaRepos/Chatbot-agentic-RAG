import logging
from app.logger_service.handlers import HTTPLogHandler
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI
from contextlib import asynccontextmanager
from langchain_community.vectorstores import FAISS

from .database import init_db, get_db, seed_embedding_models, seed_default_store
from . import schemas, crud
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

import os
from pathlib import Path

LOGGER_SERVICE_URL = os.environ.get("LOGGER_SERVICE_URL", "http://localhost:8004")
PATH_TO_FAISS_INDEX = os.environ.get("PATH_TO_FAISS_INDEX", str(Path(__file__).resolve().parent.parent.parent.parent / "data/stores/default_index_phones"))
MODEL_NAME_EMBEDDING = os.environ.get("MODEL_NAME_EMBEDDING", "")
DEFAULT_K = int(os.environ.get("NUMBER_OF_DOCUMENTS_TO_RETRIEVE", 10))

logger = logging.getLogger("retriever_service")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
remote = HTTPLogHandler(LOGGER_SERVICE_URL)
logger.addHandler(remote)
logger.setLevel(logging.INFO)

STORE_NOT_FOUND = "Vector store not found"
loaded_stores: dict[int, FAISS] = {}

class SearchRequest(BaseModel):
    query: str
    k: int | None = None

def get_store_index(store_id: int, index_path: str) -> FAISS:
    """Load and cache FAISS index for a given store ID."""
    if store_id not in loaded_stores:
        logger.info("Loading FAISS index for store %d from %s", store_id, index_path)  
        loaded_stores[store_id] = FAISS.load_local(
            index_path, 
            embeddings,
            allow_dangerous_deserialization=True
        )  
    return loaded_stores[store_id]

def invalidate_store_index(store_id: int):
    """Invalidate cached FAISS index for a given store ID."""
    if store_id in loaded_stores:
        loaded_stores.pop(store_id)
        logger.info("Invalidated cached FAISS index for store %d", store_id)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store, embeddings
    
    logger.info("Loading embeddings model: %s", MODEL_NAME_EMBEDDING)
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)

    init_db()
    seed_embedding_models()
    seed_default_store()
    
    vector_store = FAISS.load_local(
        PATH_TO_FAISS_INDEX,
        embeddings,
        allow_dangerous_deserialization=True
    )
    logger.info("Retriever API started and default vector store loaded.")
    try:
        yield
    finally:
        logger.info("retriever API shutting down.")

app = FastAPI(lifespan=lifespan)
    
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ======= Retrieval endpoint for LLM =======
@app.post("/stores/retrieve_string")
def retrieve_documents_as_string(store_id: int, request: SearchRequest, db: Session = Depends(get_db)) -> dict:
    """Retrieve documents as a concatenated string based on the search query."""
    logger.info("retrieve_string called for store_id=%d, query='%s'", store_id, request.query[:50])
    store = crud.get_store(db, store_id) 
    if not store:
        logger.warning("Store %d not found for retrieve_string", store_id)
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    
    k = request.k or DEFAULT_K
    index = get_store_index(store_id, str(store.index_path))
    retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": k})
    docs = retriever.invoke(request.query)
    
    complete_doc_string = ""
    for doc in docs:
        complete_doc_string += doc.page_content + "\n"
    logger.info("retrieve_string returned %d docs for store_id=%d", len(docs), store_id)
    return {"documents": complete_doc_string}

# ======= Embedding Models =======
@app.get("/embedding-models", response_model=List[schemas.EmbeddingModelResponse])
def list_embedding_models(db: Session = Depends(get_db)):
    """API endpoint to list all available embedding models."""
    logger.debug("Listing embedding models")
    return crud.get_embedding_models(db)

# ======= Vector Stores CRUD =======
@app.get("/stores", response_model=List[schemas.VectorStoreResponse])
def list_stores(db: Session = Depends(get_db)):
    """API endpoint to list all vector stores."""
    logger.debug("Listing all stores")
    return crud.get_stores(db)

@app.post("/stores", response_model=schemas.VectorStoreResponse, status_code=201)
def create_store(store: schemas.VectorStoreCreate, db: Session = Depends(get_db)):
    """API endpoint to create a new vector store."""
    logger.info("Creating store: name='%s', embedding_model_id=%d", store.name, store.embedding_model_id)
    created = crud.create_store(db, store)
    logger.info("Created store id=%d, path='%s'", created.id, created.index_path)
    return created

@app.get("/stores/{store_id}", response_model=schemas.VectorStoreResponse)
def get_store(store_id: int, db: Session = Depends(get_db)):
    """API endpoint to get a vector store by its ID."""
    logger.debug("Getting store id=%d", store_id)
    store = crud.get_store(db, store_id)
    if not store:
        logger.warning("Store %d not found", store_id)
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    return store

@app.put("/stores/{store_id}", response_model=schemas.VectorStoreResponse)
def update_store(store_id: int, store_update: schemas.VectorStoreUpdate, db: Session = Depends(get_db)):
    """API endpoint to update a vector store."""
    logger.info("Updating store id=%d", store_id)
    store = crud.update_store(db, store_id, store_update)
    if not store:
        logger.warning("Store %d not found for update", store_id)
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    logger.info("Updated store id=%d, name='%s'", store_id, store.name)
    return store

@app.delete("/stores/{store_id}", status_code=204)
def delete_store(store_id: int, db: Session = Depends(get_db)):
    """API endpoint to delete a vector store."""
    logger.info("Deleting store id=%d", store_id)
    invalidate_store_index(store_id)
    if not crud.delete_store(db, store_id):
        logger.warning("Store %d not found for deletion", store_id)
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    logger.info("Deleted store id=%d", store_id)

# ======= Retrieval Endpoint =======
@app.post("/stores/{store_id}/retrieve", response_model=schemas.RetrievalResponse)
async def retrieve_from_store(store_id: int, request: schemas.RetrievalRequest, db: Session = Depends(get_db)):
    """API endpoint to retrieve documents from a specific vector store."""
    logger.info("Retrieve called for store_id=%d, query='%s', k=%d", store_id, request.query[:50], request.k)
    store = crud.get_store(db, store_id)
    if not store:
        logger.warning("Store %d not found for retrieval", store_id)
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    
    index = get_store_index(store_id, str(store.index_path))
    
    results = index.similarity_search_with_score(request.query, k=request.k)
    logger.info("Retrieved %d chunks from store_id=%d", len(results), store_id)
    
    chunks = [
        schemas.RetrievedChunk(
            content=doc.page_content,
            score=float(score),
            metadata=doc.metadata
        ) for doc, score in results
    ]
    
    return schemas.RetrievalResponse(
        chunks=chunks, 
        store_id=store_id,
        store_name=str(store.name)
        )