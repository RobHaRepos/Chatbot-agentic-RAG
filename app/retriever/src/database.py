import logging
import os

from sqlalchemy import JSON, create_engine, Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

logger = logging.getLogger("retriever_service")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///.data/vector_stores.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ======= Database Models =======
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
    templates = relationship("PromptTemplate", back_populates="store", cascade="all, delete-orphan")    
    
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
    """Create the default store entry."""
    db = SessionLocal()
    try:
        existing = db.query(VectorStore).filter(VectorStore.name == "default_store").first()
        if not existing:
            embedding_model = db.query(EmbeddingModel).filter(
                EmbeddingModel.name == "all-MiniLM-L6-v2"
            ).first()
            
            if embedding_model:
                default_store = VectorStore(
                    name="default_store",
                    description="Default phone documentation index (migrated)",
                    index_path="data/stores/default_store",
                    embedding_model_id=embedding_model.id,
                    is_active=True
                )
                db.add(default_store)
                db.commit()
                logger.info("Created default store: default_store")
                try:
                    index_path = str(default_store.index_path)
                    os.makedirs(index_path, exist_ok=True)
                except Exception:
                    logger.warning("Could not create index directory for default store: %s", default_store.index_path)
        else:
            try:
                index_path_existing = str(existing.index_path)
                if not os.path.exists(index_path_existing):
                    logger.warning("Default store exists in DB but index folder missing at %s. Creating directory only.", index_path_existing)
                    os.makedirs(index_path_existing, exist_ok=True)
            except Exception:
                logger.warning("Could not ensure index path for default store: %s", getattr(existing, "index_path", "<unknown>"))
    finally:
        db.close()

# ======= Prompt Database Model =======
class PromptTemplate(Base):
    """Schema for database table storing prompt templates used in LLM interactions."""
    __tablename__ = "prompt_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    template_type = Column(String(100), nullable=False)
    store_id = Column(Integer, ForeignKey("vector_stores.id"), nullable=False)
    messages = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    
    store = relationship("VectorStore", back_populates="templates")


# ======= Generic Default Templates (for new stores) =======
DEFAULT_TEMPLATES = {
    "retrieve_or_respond": {
        "name": "Default - Retrieve or Respond",
        "messages": [
            {"role": "system", "content": (
                "You are a helpful AI assistant. Given the user question, "
                "decide if you need to search for more information or can respond directly.\n"
                "If the question is unclear or needs clarification:\n"
                '{{"action":"clarify","answer":"<your clarification request>"}}\n'
                "If you need to search for information:\n"
                '{{"action":"retrieve", "query":"<focused search query>"}}\n'
                "Return only valid JSON."
            )},
            {"role": "user", "content": "User question: {user_input}"}
        ]
    },
    "generate_answer": {
        "name": "Default - Generate Answer",
        "messages": [
            {"role": "system", "content": (
                "You are a helpful AI assistant. "
                "Answer the user's question based on the retrieved information.\n"
                "If you need more information to fully answer:\n"
                '{{"action":"retrieve","query":"<focused search query>", "context": "<summary of what you know so far>"}}\n'
                "If you have all the information needed, provide a clear answer as plain text.\n"
                "USER QUESTION: {user_input}\n"
                "RETRIEVED INFORMATION: {retrieved_information}\n"
                "CONTEXT: {context}\n"
                "Don't make up information that isn't in the documents."
            )}
        ]
    }
}

# ======= Phone Store Default Templates =======
PHONE_STORE_TEMPLATES = {
    "retrieve_or_respond": {
        "name": "Phone Store - Retrieve or Respond",
        "messages": [
            {"role": "system", "content": (
                "You are a helpful AI assistant for a phone shop. Given the user question, "
                "decide if you need clarification from the user or if you need to search for more information. "
                "If the user question is unrelated to phones: \n"
                '{{"action":"clarify","answer":"<Create answer to let user clarify>"}}\n'
                "If the user question is related to phones follow the steps:\n"
                "1. step: Determine if there are several distinct different parts to the user query.\n"
                "2. step: If there are multiple parts, choose just one part, which is the most relevant to answer first.\n"
                "3. step: write a RAG query to retrieve more information about that part.\n"
                '{{"action":"retrieve", "query":"<short RAG query — focused always just on one of the missing information pieces>"}}\n'
                "Return only valid JSON in the response body.\n"
                "Example: What is the newest phone, what display does it have and what cameras?\n"
                "First priority for example: model of the newest phone.\n"
            )},
            {"role": "user", "content": "User question: {user_input}"}
        ]
    },
    "generate_answer": {
        "name": "Phone Store - Generate Answer",
        "messages": [
            {"role": "system", "content": (
                "You are a helpful AI assistant for a phone shop. "
                "Given the user question, retrieved document information, and past context, do the following steps:\n"
                "Step 1: Evaluate, if you can answer all parts of the user question.\n"
                "Step 2: Consider the rules:\n"
                "1. If multiple models in the documents, prefer the one named in context as 'Newest'.\n"
                "2. Use documents only when they unambiguously match the model.\n"
                "3. Mind about SINGULAR/plural forms in user question and documents.\n"
                "Step 3: If you CANNOT answer all parts of the user question:\n"
                "First: separate each part of the user question that you cannot answer with the given information.\n"
                "Second: Write a RAG query that focuses on just ONE of the missing information pieces.\n"
                "Third: RETURN ONLY a single JSON object that strictly conforms to this exact schema:\n"
                '{{"action":"retrieve","query":"<short RAG query — focused always just on one of the missing information pieces>", "context": "<concatenated and summarized infos of all for the user question relevant infos>"}}\n\n'
                "Step 4: If you have ALL information to answer ALL parts of the user question, "
                "return a concise, accurate answer as plain text.\n"
                "USER QUESTION: {user_input}\n"
                "INFORMATION FROM DOCUMENTS: {retrieved_information}\n"
                "CONTEXT: {context}\n"
                "Don't make up an answer.\n"
                "Example:\n"
                "User question: What is the newest Iphone and what display does it have?\n"
                "retrieved Docs: Iphone 13 and released 2022\n"
                '{{"action":"retrieve","query":"Display of the Iphone 13", "context": "Newest Iphone is Iphone 13, Released 2022"}}\n\n'
            )}
        ]
    }
}


def _seed_template_if_missing(db, store_id: int, template_type: str, template_config: dict) -> bool:
    """Helper to seed a single template if it doesn't exist. Returns True if created."""
    existing = db.query(PromptTemplate).filter(
        PromptTemplate.store_id == store_id,
        PromptTemplate.template_type == template_type
    ).first()
    
    if existing:
        return False
    
    db.add(PromptTemplate(
        name=template_config["name"],
        template_type=template_type,
        store_id=store_id,
        messages=template_config["messages"],
        is_active=True
    ))
    return True


def seed_default_templates_for_store(db, store_id: int, store_name: str):
    """Seed default templates for any new vector store. """
    templates_to_use = PHONE_STORE_TEMPLATES if store_name == "default_store" else DEFAULT_TEMPLATES
    
    for template_type, config in templates_to_use.items():
        if _seed_template_if_missing(db, store_id, template_type, config):
            logger.info("Created %s template for store '%s'", template_type, store_name)


def seed_phone_store_templates():
    """Seed templates specifically for the default phone store."""
    db = SessionLocal()
    try:
        phone_store = db.query(VectorStore).filter(
            VectorStore.name == "default_store"
        ).first()
        
        if not phone_store:
            logger.warning("Phone store not found, skipping template seeding")
            return
        
        store_id: int = phone_store.id  # type: ignore[assignment]
        seed_default_templates_for_store(db, store_id, "default_store")
        
        db.commit()
    finally:
        db.close()