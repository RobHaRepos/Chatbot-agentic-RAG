"""Tests for database models and seeding functions."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a fresh in-memory test database."""
    from app.rag.src.database import Base, EmbeddingModel, VectorStore, Document

    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = test_session_local()
    yield db, engine, EmbeddingModel, VectorStore, Document

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class TestEmbeddingModel:
    """Tests for EmbeddingModel table."""

    def test_create_embedding_model(self, test_db):
        """Can create an embedding model."""
        db, _, embedding_model, _, _ = test_db

        model = embedding_model(
            name="test-model",
            display_name="Test Model",
            dimension=384,
            description="A test model",
            is_available=True,
        )
        db.add(model)
        db.commit()

        result = db.query(embedding_model).filter(embedding_model.name == "test-model").first()
        assert result is not None
        assert result.dimension == 384
        assert result.is_available is True

    def test_embedding_model_unique_name(self, test_db):
        """Embedding model name must be unique."""
        db, _, embedding_model, _, _ = test_db
        from sqlalchemy.exc import IntegrityError

        model1 = embedding_model(name="unique", display_name="A", dimension=100)
        db.add(model1)
        db.commit()

        model2 = embedding_model(name="unique", display_name="B", dimension=200)
        db.add(model2)

        with pytest.raises(IntegrityError):
            db.commit()


class TestVectorStore:
    """Tests for VectorStore table."""

    def test_create_vector_store(self, test_db):
        """Can create a vector store with embedding model."""
        db, _, embedding_model, vector_store, _ = test_db

        model = embedding_model(name="model", display_name="Model", dimension=384)
        db.add(model)
        db.commit()

        store = vector_store(
            name="my-store",
            description="Test store",
            index_path="data/stores/my_store",
            embedding_model_id=model.id,
            is_active=True,
        )
        db.add(store)
        db.commit()

        result = db.query(vector_store).filter(vector_store.name == "my-store").first()
        assert result is not None
        assert result.embedding_model_id == model.id
        assert result.document_count == 0

    def test_vector_store_embedding_model_relationship(self, test_db):
        """VectorStore has relationship to EmbeddingModel."""
        db, _, embedding_model, vector_store, _ = test_db

        model = embedding_model(name="related-model", display_name="Related", dimension=768)
        db.add(model)
        db.commit()

        store = vector_store(
            name="store-with-model",
            index_path="path",
            embedding_model_id=model.id,
        )
        db.add(store)
        db.commit()

        result = db.query(vector_store).first()
        assert result.embedding_model.name == "related-model"


class TestDocument:
    """Tests for Document table."""

    def test_create_document(self, test_db):
        """Can create a document linked to a store."""
        db, _, embedding_model, vector_store, document = test_db

        model = embedding_model(name="m", display_name="M", dimension=100)
        db.add(model)
        db.commit()

        store = vector_store(name="s", index_path="p", embedding_model_id=model.id)
        db.add(store)
        db.commit()

        doc = document(
            store_id=store.id,
            filename="test.pdf",
            file_type="pdf",
            file_size=1024,
            chunk_count=10,
        )
        db.add(doc)
        db.commit()

        result = db.query(document).first()
        assert result.filename == "test.pdf"
        assert result.store_id == store.id

    def test_document_cascade_delete(self, test_db):
        """Deleting store cascades to delete documents."""
        db, _, embedding_model, vector_store, document = test_db

        model = embedding_model(name="m", display_name="M", dimension=100)
        db.add(model)
        db.commit()

        store = vector_store(name="s", index_path="p", embedding_model_id=model.id)
        db.add(store)
        db.commit()

        doc = document(store_id=store.id, filename="doc.txt")
        db.add(doc)
        db.commit()

        db.delete(store)
        db.commit()

        assert db.query(document).count() == 0


class TestSeedFunctions:
    """Tests for database seeding functions."""

    def test_seed_embedding_models_creates_models(self, test_db, monkeypatch):
        """seed_embedding_models() creates models if they don't exist."""
        db, engine, embedding_model, _, _ = test_db

        from app.rag.src import database

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        database.seed_embedding_models()

        models = db.query(embedding_model).all()
        assert len(models) >= 2

        names = [m.name for m in models]
        assert "all-MiniLM-L6-v2" in names
        assert "all-mpnet-base-v2" in names

    def test_seed_embedding_models_idempotent(self, test_db, monkeypatch):
        """Calling seed_embedding_models() twice doesn't duplicate."""
        db, engine, embedding_model, _, _ = test_db

        from app.rag.src import database

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        database.seed_embedding_models()
        database.seed_embedding_models()

        count = db.query(embedding_model).count()
        assert count == 2

    def test_seed_default_store_creates_store(self, test_db, monkeypatch):
        """seed_default_store() creates the default store."""
        db, engine, _, vector_store, _ = test_db
        from app.rag.src import database

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)
        
        database.seed_embedding_models()
        database.seed_default_store()

        store = (
            db.query(vector_store)
            .filter(vector_store.name == "default_index_phones")
            .first()
        )
        assert store is not None
        assert "default_index_phones" in store.index_path

    def test_seed_default_store_idempotent(self, test_db, monkeypatch):
        """Calling seed_default_store() twice doesn't duplicate."""
        db, engine, _, vector_store, _ = test_db

        from app.rag.src import database

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        database.seed_embedding_models()
        database.seed_default_store()
        database.seed_default_store()

        count = (
            db.query(vector_store)
            .filter(vector_store.name == "default_index_phones")
            .count()
        )
        assert count == 1
