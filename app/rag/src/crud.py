import os
import shutil
from sqlalchemy.orm import Session
from typing import List, Optional
from . import database
from .database import EmbeddingModel, VectorStore, Document
from .schemas import VectorStoreCreate, VectorStoreUpdate, DocumentCreate

DATA_DIR = os.getenv("VECTOR_STORE_DATA_DIR", "./data/stores")

def get_embedding_models(db: Session) -> List[EmbeddingModel]:
    """Retrieve all available embedding models from the database."""
    return db.query(EmbeddingModel).filter(EmbeddingModel.is_available).all()

def get_embedding_model(db: Session, model_id: int) -> Optional[EmbeddingModel]:
    """Retrieve a specific embedding model by its ID."""
    return db.query(EmbeddingModel).filter(EmbeddingModel.id == model_id).first()

def create_store(db: Session, store: VectorStoreCreate) -> VectorStore:
    """Create a new vector store in the database and set up its unique storage directory."""
    index_path = os.path.join(DATA_DIR, f"store_{store.name.replace(' ', '_').lower()}")
    os.makedirs(index_path, exist_ok=True)
    
    db_store = VectorStore(
        name=store.name,
        description=store.description,
        index_path=index_path,
        embedding_model_id=store.embedding_model_id
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    
    return db_store

def get_stores(db: Session, skip: int = 0, limit: int = 100) -> List[VectorStore]:
    """Retrieve a list of vector stores with pagination."""
    return db.query(VectorStore).offset(skip).limit(limit).all()

def get_store(db: Session, store_id: int) -> Optional[VectorStore]:
    """Retrieve a specific vector store by its ID."""
    return db.query(VectorStore).filter(VectorStore.id == store_id).first()

def update_store(db: Session, store_id: int, store_update: VectorStoreUpdate) -> Optional[VectorStore]:
    """Update an existing vector store's details."""
    db_store = get_store(db, store_id)
    if not db_store:
        return None
    
    update_data = store_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_store, key, value)
    
    db.commit()
    db.refresh(db_store)
    return db_store

def delete_store(db: Session, store_id: int) -> bool:
    """Delete a vector store and its associated data directory."""
    db_store = get_store(db, store_id)
    if not db_store:
        return False

    if os.path.exists(str(db_store.index_path)):
        shutil.rmtree(str(db_store.index_path))
    
    db.delete(db_store)
    db.commit()
    return True

def create_document(db: Session, document: DocumentCreate) -> Document:
    """Create a new document record associated with a vector store."""
    doc = database.Document(**document.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_documents(db: Session, store_id: int) -> List[Document]:
    """Retrieve all documents for a specific vector store."""
    return db.query(database.Document).filter(database.Document.store_id == store_id).all()

def get_document(db: Session, doc_id: int) -> Optional[Document]:
    """Retrieve a specific document by its ID."""
    return db.query(database.Document).filter(database.Document.id == doc_id).first()

def delete_document(db: Session, doc_id: int) -> bool:
    """Delete a document record."""
    doc = get_document(db, doc_id)
    if not doc:
        return False
    
    db.delete(doc)
    db.commit()
    return True

def update_store_stats(db: Session, store_id: int):
    """Update the document and chunk counts for a vector store."""
    store = db.query(VectorStore).filter(VectorStore.id == store_id).first()
    if store:
        docs = db.query(database.Document).filter(database.Document.store_id == store_id).all()
        setattr(store, 'document_count', len(docs))
        setattr(store, 'chunk_count', sum(doc.chunk_count for doc in docs))
        db.commit()        