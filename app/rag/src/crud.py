import os
import shutil
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import EmbeddingModel, VectorStore, Document
from .schemas import VectorStoreCreate, VectorStoreUpdate

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

def create_document(db: Session, store_id: int, filename: str, filetype: str, filesize: int) -> Document:
    """Create a new document record associated with a vector store."""
    doc = Document(
        store_id=store_id,
        filename=filename,
        file_type=filetype,
        file_size=filesize,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_store_documents(db: Session, store_id: int) -> List[Document]:
    """Retrieve all documents associated with a specific vector store."""
    return db.query(Document).filter(Document.store_id == store_id).all()
        