import os
import shutil
from typing import List, Optional

from sqlalchemy.orm import Session

from . import database
from .database import Document, EmbeddingModel, PromptTemplate, VectorStore, seed_default_templates_for_store
from .schemas import DocumentCreate, TemplateCreateIn, TemplateUpdateIn, VectorStoreCreate, VectorStoreUpdate

DATA_DIR = os.getenv("VECTOR_STORE_DATA_DIR", "./data/stores")

# ======= CRUD Operations Vector Stores and Documents =======
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
    
    # Seed default templates for the new store
    seed_default_templates_for_store(db, db_store.id, db_store.name)  # type: ignore[arg-type]
    db.commit()
    
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
        
        
# ======== CRUD Operations Prompt Templates =========     
def get_templates_by_store(db: Session, store_id: int, template_type: str | None = None) -> List[PromptTemplate]:
    """Retrieve all active templates for a store, optionally filtered by type."""
    query = db.query(PromptTemplate).filter(
        PromptTemplate.store_id == store_id,
        PromptTemplate.is_active
    )
    
    if template_type:
        query = query.filter(PromptTemplate.template_type == template_type)
    return query.all()

def get_template(db: Session, template_id: int) -> Optional[PromptTemplate]:
    """Retrieve a specific prompt template by its ID."""
    return db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

def get_template_by_store_and_type(db: Session, store_id: int, template_type: str) -> Optional[PromptTemplate]:
    """Retrieve an active prompt template by store ID and template type."""
    return db.query(PromptTemplate).filter(
        PromptTemplate.store_id == store_id,
        PromptTemplate.template_type == template_type,
        PromptTemplate.is_active
    ).first()
    
def create_template(db: Session, template: TemplateCreateIn) -> PromptTemplate:
    """Create a new prompt template."""
    store = get_store(db, template.store_id)
    if not store:
        raise ValueError(f"Store with id {template.store_id} does not exist.")
    
    db_template = PromptTemplate(
        name=template.name,
        template_type=template.template_type.value,
        store_id=template.store_id,
        messages=[msg.model_dump() for msg in template.messages],
        is_active=True
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template

def update_template(db: Session, template_id: int, template_update: TemplateUpdateIn) -> Optional[PromptTemplate]:
    """Update an existing prompt template's details."""
    db_template = get_template(db, template_id)
    if not db_template:
        return None
    
    update_data = template_update.model_dump(exclude_unset=True)
    
    if template_update.messages is not None:
        update_data["messages"] = [msg.model_dump() for msg in template_update.messages]
        
    for key, value in update_data.items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    
    return db_template

def delete_template(db: Session, template_id: int) -> bool:
    """Delete a prompt template by its ID."""
    db_template = get_template(db, template_id)
    if not db_template:
        return False
    
    db.delete(db_template)
    db.commit()
    
    return True