import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///.data/vector_stores.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EmbeddingModel(Base):
    """Stores available embedding models. Each with a dimension field due to different vector sizes."""
    __tablename__ = "embedding_models"
    
    id = Column(Integer, unique=True, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255))
    dimension = Column(Integer, nullable=False)
    description = Column(Text)
    is_available = Column(Boolean, default=True)
    
    stores = relationship("VectorStore", back_populates="embedding_model")
    
class VectorStore(Base):
    """Represents FAISS index. Tracks name, description, associated embedding model, and stats."""
    __tablename__ = "vector_stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    embedding_model_id = Column(Integer, ForeignKey("embedding_models.id"), nullable=False)
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    index_path = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)

    embedding_model = relationship("EmbeddingModel", back_populates="stores")
    documents = relationship("Document", back_populates="store", cascade="all, delete-orphan")
    
class Document(Base):
    """
    Tracks uploaded files. Links to vector store, filename, type, 
    size, chunk count, processingstatus, and errors.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("vector_stores.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    chunk_count = Column(Integer, default=0)
    
    store = relationship("VectorStore", back_populates="documents")
    
def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)
    
def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def seed_embedding_models():
    """Seed the database with initial embedding models if they don't exist."""
    db = SessionLocal()
    try: 
        models = [
            {"name": "all-MiniLM-L6-v2", "display_name": "MiniLM L6 (Fast)", "dimension": 384, "description": "Fast, lightweight model"},
            {"name": "all-mpnet-base-v2", "display_name": "MPNet Base (Balanced)", "dimension": 768, "description": "Best quality/speed tradeoff"},
        ]
        
        for model_data in models:
            exists = db.query(EmbeddingModel).filter(EmbeddingModel.name == model_data["name"]).first()
            if not exists:
                db.add(EmbeddingModel(**model_data))
        
        db.commit()
    finally:
        db.close()
        
def seed_default_store():
    """Create the default store entry for the migrated FAISS index."""
    db = SessionLocal()
    try:
        existing = db.query(VectorStore).filter(VectorStore.name == "default_index_phones").first()
        if not existing:
            embedding_model = db.query(EmbeddingModel).filter(
                EmbeddingModel.name == "all-MiniLM-L6-v2"
            ).first()
            
            if embedding_model:
                default_store = VectorStore(
                    name="default_index_phones",
                    description="Default phone documentation index (migrated)",
                    index_path="data/stores/default_index_phones",
                    embedding_model_id=embedding_model.id,
                    is_active=True
                )
                db.add(default_store)
                db.commit()
                print("Created default store: default_index_phones")
    finally:
        db.close()