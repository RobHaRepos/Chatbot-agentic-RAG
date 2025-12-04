"""Tests for database models and seeding functions."""
import logging

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.retriever.src import database
from app.retriever.src.database import Base, Document, EmbeddingModel, PromptTemplate, VectorStore

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a fresh in-memory test database."""

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

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        database.seed_embedding_models()
        database.seed_embedding_models()

        count = db.query(embedding_model).count()
        assert count == 2

    def test_seed_default_store_creates_store(self, test_db, monkeypatch):
        """seed_default_store() creates the default store."""
        db, engine, _, vector_store, _ = test_db

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)
        
        database.seed_embedding_models()
        database.seed_default_store()

        store = (
            db.query(vector_store)
            .filter(vector_store.name == "default_store")
            .first()
        )
        assert store is not None
        assert "default_store" in store.index_path
    def test_seed_default_store_idempotent(self, test_db, monkeypatch):
        """Calling seed_default_store() twice doesn't duplicate."""
        db, engine, _, vector_store, _ = test_db

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        database.seed_embedding_models()
        database.seed_default_store()
        database.seed_default_store()

        count = (
            db.query(vector_store)
            .filter(vector_store.name == "default_store")
            .count()
        )
        assert count == 1


class TestSeedTemplateIfMissing:
    """Tests for the _seed_template_if_missing helper function."""

    def test_creates_template_when_missing(self, test_db):
        """_seed_template_if_missing creates template when it doesn't exist."""
        db, _, _, _, _ = test_db

        # First create an embedding model (required by VectorStore)
        model = EmbeddingModel(
            name="test_model",
            dimension=384
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        # Then create a store to reference
        store = VectorStore(
            name="test_store",
            index_path="/test/path",
            embedding_model_id=model.id,
        )
        db.add(store)
        db.commit()
        db.refresh(store)

        template_config = {
            "name": "Test Template",
            "messages": [{"role": "system", "content": "Test"}],
        }

        result = database._seed_template_if_missing(
            db, store.id, "test_type", template_config # type: ignore[assignment]
        )
        db.commit()

        assert result is True
        template = db.query(PromptTemplate).filter(
            PromptTemplate.store_id == store.id,
            PromptTemplate.template_type == "test_type"
        ).first()
        assert template is not None
        assert template.name == "Test Template"
        assert template.is_active is True

    def test_returns_false_when_exists(self, test_db):
        """_seed_template_if_missing returns False when template already exists."""
        db, _, _, _, _ = test_db

        # First create an embedding model
        model = EmbeddingModel(
            name="test_model",
            dimension=384
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        # Create store and existing template
        store = VectorStore(
            name="test_store",
            index_path="/test/path",
            embedding_model_id=model.id,
        )
        db.add(store)
        db.commit()
        db.refresh(store)

        existing_template = PromptTemplate(
            name="Existing Template",
            template_type="test_type",
            store_id=store.id,
            messages=[{"role": "system", "content": "Existing"}],
            is_active=True,
        )
        db.add(existing_template)
        db.commit()

        template_config = {
            "name": "New Template",
            "messages": [{"role": "system", "content": "New"}],
        }

        result = database._seed_template_if_missing(
            db, store.id, "test_type", template_config # type: ignore[assignment]
        )

        assert result is False
        # Verify original template unchanged
        templates = db.query(PromptTemplate).filter(
            PromptTemplate.store_id == store.id,
            PromptTemplate.template_type == "test_type"
        ).all()
        assert len(templates) == 1
        assert templates[0].name == "Existing Template"


class TestSeedPhoneStoreTemplates:
    """Tests for the seed_phone_store_templates function."""

    def test_seeds_templates_for_phone_store(self, test_db, monkeypatch):
        """seed_phone_store_templates creates all default templates."""
        db, engine, _, vector_store, _ = test_db

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        # Seed prerequisites first
        database.seed_embedding_models()
        database.seed_default_store()

        # Now seed templates
        database.seed_phone_store_templates()

        phone_store = db.query(vector_store).filter(
            vector_store.name == "default_store"
        ).first()
        assert phone_store is not None

        templates = db.query(PromptTemplate).filter(
            PromptTemplate.store_id == phone_store.id
        ).all()

        # Should have all template types from PHONE_STORE_TEMPLATES
        template_types = {t.template_type for t in templates}
        assert "retrieve_or_respond" in template_types
        assert "generate_answer" in template_types

    def test_skips_when_store_not_found(self, test_db, monkeypatch, caplog):
        """seed_phone_store_templates skips if phone store doesn't exist."""
        db, engine, _, _, _ = test_db

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        with caplog.at_level(logging.WARNING):
            database.seed_phone_store_templates()

        assert "Phone store not found" in caplog.text

        # Verify no templates created
        template_count = db.query(PromptTemplate).count()
        assert template_count == 0

    def test_seed_templates_idempotent(self, test_db, monkeypatch):
        """Calling seed_phone_store_templates twice doesn't duplicate templates."""
        db, engine, _, vector_store, _ = test_db

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        # Seed prerequisites
        database.seed_embedding_models()
        database.seed_default_store()

        # Call twice
        database.seed_phone_store_templates()
        database.seed_phone_store_templates()

        phone_store = db.query(vector_store).filter(
            vector_store.name == "default_store"
        ).first()

        templates = db.query(PromptTemplate).filter(
            PromptTemplate.store_id == phone_store.id
        ).all()

        # Should still have exactly 2 templates (system and rag)
        assert len(templates) == 2

    def test_logs_when_creating_template(self, test_db, monkeypatch, caplog):
        """seed_phone_store_templates logs when creating new templates."""
        _, engine, _, _, _ = test_db

        test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(database, "SessionLocal", test_session)

        database.seed_embedding_models()
        database.seed_default_store()
        
        with caplog.at_level(logging.INFO):
            database.seed_phone_store_templates()

        # seed_default_store already calls seed_default_templates_for_store, so
        # templates are created with the new generic log format
        assert "Created retrieve_or_respond template for store" in caplog.text
        assert "Created generate_answer template for store" in caplog.text
