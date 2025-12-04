import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import crud, database, schemas
from .constants import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_K,
    LOGGER_SERVICE_URL,
    METADATA_CHUNK_INDEX,
    METADATA_DOCUMENT_ID,
    MODEL_NAME_EMBEDDING,
    STORE_NOT_FOUND,
    TEMPLATE_NOT_FOUND,
)
from .database import get_db, init_db, seed_default_store, seed_embedding_models, seed_phone_store_templates
from .faiss_utils import (
    filter_and_collect_chunks,
    get_store_index,
    get_store_or_404,
    invalidate_store_index,
    process_file_into_chunks,
    read_and_decode_file,
    rebuild_index_with_new_content,
    remove_index_files,
    save_and_invalidate_index,
    update_index_filenames,
    validate_document_ownership,
    validate_upload_file,
)
from app.logger_service.handlers import HTTPLogHandler

logger = logging.getLogger("retriever_service")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
remote = HTTPLogHandler(LOGGER_SERVICE_URL)
logger.addHandler(remote)
logger.setLevel(logging.DEBUG)

# Global embeddings variable - initialized during lifespan
embeddings = None


class SearchRequest(BaseModel):
    query: str
    k: int | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global embeddings
    
    logger.info(f"Loading embeddings model: {MODEL_NAME_EMBEDDING}")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME_EMBEDDING)

    init_db()
    seed_embedding_models()
    seed_default_store()
    seed_phone_store_templates()
    
    logger.info("Retriever API started.")
    try:
        yield
    finally:
        logger.info("Retriever API shutting down.")

app = FastAPI(lifespan=lifespan)
    
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ======= Retrieval endpoint for LLM =======
@app.post("/stores/retrieve_string")
def retrieve_documents_as_string(store_id: int, request: SearchRequest, db: Session = Depends(get_db)) -> dict:
    """Retrieve documents as a concatenated string based on the search query."""
    logger.info(f"retrieve_string called for store_id={store_id}, query='{request.query[:50]}'")
    store = get_store_or_404(db, store_id)
    
    k = request.k or DEFAULT_K
    index = get_store_index(store_id, str(store.index_path), embeddings)
    if index is None:
        logger.info(f"No documents in store {store_id} yet")
        return {"documents": ""}
    
    retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": k})
    docs = retriever.invoke(request.query)
    
    complete_doc_string = "\n".join(doc.page_content for doc in docs)
    logger.info(f"retrieve_string returned {len(docs)} docs for store_id={store_id}")
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
    logger.info(f"Creating store: name='{store.name}', embedding_model_id={store.embedding_model_id}")
    created = crud.create_store(db, store)
    logger.info(f"Created store id={created.id}, path='{created.index_path}'")
    return created

@app.get("/stores/{store_id}", response_model=schemas.VectorStoreResponse)
def get_store_endpoint(store_id: int, db: Session = Depends(get_db)):
    """API endpoint to get a vector store by its ID."""
    logger.debug(f"Getting store id={store_id}")
    store = get_store_or_404(db, store_id)
    return store

@app.patch("/stores/{store_id}", response_model=schemas.VectorStoreResponse)
def update_store_endpoint(store_id: int, store_update: schemas.VectorStoreUpdate, db: Session = Depends(get_db)):
    """API endpoint to update a vector store."""
    logger.info(f"Updating store id={store_id}")
    store = crud.update_store(db, store_id, store_update)
    if not store:
        logger.info(f"Store {store_id} not found for update")
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    logger.info(f"Updated store id={store_id}, name='{store.name}'")
    return store

@app.delete("/stores/{store_id}", status_code=204)
def delete_store_endpoint(store_id: int, db: Session = Depends(get_db)):
    """API endpoint to delete a vector store."""
    logger.info(f"Deleting store id={store_id}")
    invalidate_store_index(store_id)
    if not crud.delete_store(db, store_id):
        logger.info(f"Store {store_id} not found for deletion")
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    logger.info(f"Deleted store id={store_id}")

# ======= Retrieval Endpoint =======
@app.post("/stores/{store_id}/retrieve", response_model=schemas.RetrievalResponse)
def retrieve_from_store(store_id: int, request: schemas.RetrievalRequest, db: Session = Depends(get_db)):
    """API endpoint to retrieve documents from a specific vector store."""
    logger.info(f"Retrieve called for store_id={store_id}, query='{request.query[:50]}', k={request.k}")
    store = get_store_or_404(db, store_id)
    
    index = get_store_index(store_id, str(store.index_path), embeddings)
    if index is None:
        logger.info(f"No documents in store {store_id} yet")
        return schemas.RetrievalResponse(
            chunks=[],
            store_id=store_id,
            store_name=str(store.name)
        )
    
    results = index.similarity_search_with_score(request.query, k=request.k)
    filtered_results = [(doc, score) for doc, score in results if doc.page_content.strip()]
    logger.info(f"Retrieved {len(filtered_results)} chunks from store_id={store_id} (filtered from {len(results)})")
    
    chunks = [
        schemas.RetrievedChunk(
            content=doc.page_content,
            score=float(score),
            metadata=doc.metadata
        ) for doc, score in filtered_results
    ]
    
    return schemas.RetrievalResponse(
        chunks=chunks, 
        store_id=store_id,
        store_name=str(store.name)
        )
    
# ======= Document Management =======
@app.get("/stores/{store_id}/documents", response_model=List[schemas.DocumentResponse])
def list_documents(store_id: int, db: Session = Depends(get_db)):
    """API endpoint to list all documents in a vector store."""
    logger.debug(f"Listing documents for store_id={store_id}")
    get_store_or_404(db, store_id)
    return crud.get_documents(db, store_id)

@app.get("/stores/{store_id}/documents/{doc_id}", response_model=schemas.DocumentWithContent)
def get_document(store_id: int, doc_id: int, db: Session = Depends(get_db)):
    """API endpoint to get a single document with its full content."""
    logger.debug(f"Getting document id={doc_id} from store_id={store_id}")
    
    store = get_store_or_404(db, store_id)
    
    doc = crud.get_document(db, doc_id)
    validate_document_ownership(doc, doc_id, store_id)
    
    index = get_store_index(store_id, str(store.index_path), embeddings)
    if index is None:
        logger.info(f"No index for store {store_id} - document may have been just created")
        return schemas.DocumentWithContent(
            id=doc.id,  # type: ignore[arg-type]
            filename=doc.filename,  # type: ignore[arg-type]
            file_type=doc.file_type,  # type: ignore[arg-type]
            file_size=doc.file_size,  # type: ignore[arg-type]
            chunk_count=0,
            content=""
        )
    
    all_docs = index.docstore._dict  # type: ignore[attr-defined]
    doc_chunks = []
    
    for chunk_id, doc_obj in all_docs.items():
        if not doc_obj.page_content.strip():
            continue
        if doc_obj.metadata.get(METADATA_DOCUMENT_ID) == doc_id:
            chunk_index = doc_obj.metadata.get(METADATA_CHUNK_INDEX, 0)
            doc_chunks.append((chunk_index, doc_obj.page_content))
    
    doc_chunks.sort(key=lambda x: x[0])
    content = "\n".join(chunk[1] for chunk in doc_chunks)
    
    return schemas.DocumentWithContent(
        id=doc.id,  # type: ignore[arg-type]
        filename=doc.filename,  # type: ignore[arg-type]
        file_type=doc.file_type,  # type: ignore[arg-type]
        file_size=doc.file_size,  # type: ignore[arg-type]
        chunk_count=doc.chunk_count,  # type: ignore[arg-type]
        content=content
    )

@app.patch("/stores/{store_id}/documents/{doc_id}", response_model=schemas.DocumentResponse)
def update_document(store_id: int, doc_id: int, update: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    """API endpoint to update a document (filename and/or content)."""
    logger.info(f"Updating document id={doc_id} in store_id={store_id}")
    
    store = get_store_or_404(db, store_id)
    
    doc = crud.get_document(db, doc_id)
    validate_document_ownership(doc, doc_id, store_id)
    
    index = get_store_index(store_id, str(store.index_path), embeddings)
    
    if update.content:
        filename = update.filename or str(doc.filename)  # type: ignore[union-attr]
        new_index, chunk_count = rebuild_index_with_new_content(
            index, doc_id, update.content, filename, embeddings
        )
        
        save_and_invalidate_index(new_index, str(store.index_path), store_id)
        
        if update.filename:
            doc.filename = update.filename  # type: ignore[misc]
        doc.file_size = len(update.content.encode('utf-8'))  # type: ignore[misc]
        doc.chunk_count = chunk_count  # type: ignore[misc]
        
        logger.info(f"Replaced content with {chunk_count} new chunks for doc {doc_id}")
    
    elif update.filename:
        doc.filename = update.filename  # type: ignore[misc]
        
        new_index = update_index_filenames(index, doc.id, update.filename, embeddings)  # type: ignore[arg-type]
        save_and_invalidate_index(new_index, str(store.index_path), store_id)
        
        logger.info(f"Updated filename for doc {doc_id} to '{update.filename}'")
    
    db.commit()
    db.refresh(doc)
    crud.update_store_stats(db, store_id)
    
    return doc

@app.delete("/stores/{store_id}/documents/{doc_id}", status_code=204)
def delete_document(store_id: int, doc_id: int, db: Session = Depends(get_db)):
    """API endpoint to delete a document and remove its chunks from FAISS."""
    logger.info(f"Deleting document id={doc_id} from store_id={store_id}")
    
    store = get_store_or_404(db, store_id)
    
    doc = crud.get_document(db, doc_id)
    validate_document_ownership(doc, doc_id, store_id)
    
    index = get_store_index(store_id, str(store.index_path), embeddings)
    
    chunks_to_keep, metadatas_to_keep = filter_and_collect_chunks(
        index,
        lambda doc_obj: doc_obj.metadata.get(METADATA_DOCUMENT_ID) != doc_id
    )
    
    if chunks_to_keep:
        assert embeddings is not None, "Embeddings not initialized"
        new_index = FAISS.from_texts(chunks_to_keep, embeddings, metadatas=metadatas_to_keep)
        save_and_invalidate_index(new_index, str(store.index_path), store_id)
    else:
        remove_index_files(str(store.index_path))
        invalidate_store_index(store_id)
    
    crud.delete_document(db, doc_id)
    crud.update_store_stats(db, store_id)
    
    logger.info(f"Deleted document {doc_id} and its chunks from store {store_id}")

@app.post("/stores/{store_id}/upload", response_model=List[schemas.DocumentResponse])
async def upload_document(store_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """API endpoint to upload documents to a vector store."""
    logger.info(f"Uploading {len(files)} documents to store_id={store_id}")

    store = get_store_or_404(db, store_id)
    
    index = get_store_index(store_id, str(store.index_path), embeddings)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    
    created_docs = []
    all_chunks_to_add = []
    all_metadatas_to_add = []
    
    try:
        for file in files:
            validate_upload_file(file)
            content, text = await read_and_decode_file(file)
            chunks, metadatas, doc = process_file_into_chunks(
                file, text, content, store_id, text_splitter, db
            )
            
            all_chunks_to_add.extend(chunks)
            all_metadatas_to_add.extend(metadatas)
            created_docs.append(doc)
        
        assert embeddings is not None, "Embeddings not initialized"
        if index is None:
            index = FAISS.from_texts(all_chunks_to_add, embeddings, metadatas=all_metadatas_to_add)
        else:
            index.add_texts(all_chunks_to_add, metadatas=all_metadatas_to_add)
        
        save_and_invalidate_index(index, str(store.index_path), store_id)
        db.commit()
        crud.update_store_stats(db, store_id)
        return created_docs
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        invalidate_store_index(store_id)  # Force reload from disk
        raise

# ======= Template Management =======
@app.get("/templates", response_model=List[schemas.TemplateResponse])
def list_templates(store_id: int | None = None, template_type: str | None = None, db: Session = Depends(get_db)):
    """API endpoint to list templates, optionally filtered by store and/or type."""
    logger.debug(f"Listing templates: store_id={store_id}, type={template_type}")
    
    if store_id:
        return crud.get_templates_by_store(db, store_id, template_type)
    
    query = db.query(database.PromptTemplate).filter(database.PromptTemplate.is_active)
    if template_type:
        query = query.filter(database.PromptTemplate.template_type == template_type)
    return query.all()

@app.post("/templates", response_model=schemas.TemplateResponse, status_code=201)
def create_template(template: schemas.TemplateCreateIn, db: Session = Depends(get_db)):
    """API endpoint to create a new prompt template."""
    logger.info(f"Creating template: name='{template.name}', store_id={template.store_id}")
    try:
        created = crud.create_template(db, template)
        logger.info(f"Created template id={created.id}")
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/templates/{template_id}", response_model=schemas.TemplateResponse)
def get_template_endpoint(template_id: int, db: Session = Depends(get_db)):
    """API endpoint to get a template by its ID."""
    logger.debug(f"Getting template id={template_id}")
    template = crud.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail=TEMPLATE_NOT_FOUND)
    return template

@app.patch("/templates/{template_id}", response_model=schemas.TemplateResponse)
def update_template_endpoint(
    template_id: int, 
    template_update: schemas.TemplateUpdateIn, 
    db: Session = Depends(get_db)
):
    """API endpoint to update a template."""
    logger.info(f"Updating template id={template_id}")
    template = crud.update_template(db, template_id, template_update)
    if not template:
        raise HTTPException(status_code=404, detail=TEMPLATE_NOT_FOUND)
    logger.info(f"Updated template id={template_id}")
    return template

@app.delete("/templates/{template_id}", status_code=204)
def delete_template_endpoint(template_id: int, db: Session = Depends(get_db)):
    """API endpoint to delete a template."""
    logger.info(f"Deleting template id={template_id}")
    if not crud.delete_template(db, template_id):
        raise HTTPException(status_code=404, detail=TEMPLATE_NOT_FOUND)
    logger.info(f"Deleted template id={template_id}")