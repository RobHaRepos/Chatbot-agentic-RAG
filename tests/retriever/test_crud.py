"""Tests for CRUD operations in crud.py."""
import pytest
import os
import tempfile
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.retriever.src.database import Base, EmbeddingModel, VectorStore, Document
from app.retriever.src import crud
from app.retriever.src.schemas import VectorStoreCreate, VectorStoreUpdate, DocumentCreate
from app.retriever.src.schemas import TemplateCreateIn, TemplateUpdateIn, MessageBlock, TemplateType

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db_with_crud():
    """Create test database with CRUD module patched."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = test_session_local()

    model = EmbeddingModel(
        name="test-model",
        display_name="Test",
        dimension=384,
        is_available=True,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    temp_dir = tempfile.mkdtemp()

    yield {
        "db": db,
        "crud": crud,
        "model": model,
        "temp_dir": temp_dir,
        "VectorStoreCreate": VectorStoreCreate,
        "VectorStoreUpdate": VectorStoreUpdate,
        "DocumentCreate": DocumentCreate,
        "EmbeddingModel": EmbeddingModel,
        "VectorStore": VectorStore,
        "Document": Document,
    }

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestGetEmbeddingModels:
    """Tests for get_embedding_models()."""

    def test_returns_available_models(self, test_db_with_crud):
        """Returns only available models."""
        ctx = test_db_with_crud
        db = ctx["db"]
        crud = ctx["crud"]
        embedding_model = ctx["EmbeddingModel"]

        # Add unavailable model
        unavailable = embedding_model(
            name="unavailable",
            display_name="Unavailable",
            dimension=100,
            is_available=False,
        )
        db.add(unavailable)
        db.commit()

        models = crud.get_embedding_models(db)

        names = [m.name for m in models]
        assert "test-model" in names
        assert "unavailable" not in names

    def test_returns_empty_when_none_available(self, test_db_with_crud):
        """Returns empty list when no models available."""
        ctx = test_db_with_crud
        db = ctx["db"]
        crud = ctx["crud"]

        # Make all models unavailable
        db.query(ctx["EmbeddingModel"]).update({"is_available": False})
        db.commit()

        models = crud.get_embedding_models(db)
        assert models == []


class TestGetEmbeddingModel:
    """Tests for get_embedding_model()."""

    def test_returns_model_by_id(self, test_db_with_crud):
        """Returns model when found by ID."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]

        result = crud.get_embedding_model(db, model.id)
        assert result is not None
        assert result.name == "test-model"

    def test_returns_none_when_not_found(self, test_db_with_crud):
        """Returns None when model not found."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]

        result = crud.get_embedding_model(db, 9999)
        assert result is None


class TestCreateStore:
    """Tests for create_store()."""

    def test_creates_store(self, test_db_with_crud, monkeypatch):
        """Creates store in database."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store_data = vector_store_create(
            name="new-store",
            description="Test",
            embedding_model_id=model.id,
        )

        store = crud.create_store(db, store_data)

        assert store.id is not None
        assert store.name == "new-store"
        assert store.embedding_model_id == model.id

    def test_creates_index_directory(self, test_db_with_crud, monkeypatch):
        """Creates directory for store index."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store_data = vector_store_create(
            name="dir-store",
            embedding_model_id=model.id,
        )

        store = crud.create_store(db, store_data)

        assert os.path.exists(store.index_path)


class TestGetStores:
    """Tests for get_stores()."""

    def test_returns_all_stores(self, test_db_with_crud, monkeypatch):
        """Returns all stores."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        crud.create_store(db, vector_store_create(name="s1", embedding_model_id=model.id))
        crud.create_store(db, vector_store_create(name="s2", embedding_model_id=model.id))

        stores = crud.get_stores(db)
        assert len(stores) == 2

    def test_pagination(self, test_db_with_crud, monkeypatch):
        """Supports skip and limit."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        for i in range(5):
            crud.create_store(
                db, vector_store_create(name=f"store-{i}", embedding_model_id=model.id)
            )

        stores = crud.get_stores(db, skip=2, limit=2)
        assert len(stores) == 2


class TestGetStore:
    """Tests for get_store()."""

    def test_returns_store_by_id(self, test_db_with_crud, monkeypatch):
        """Returns store when found."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        created = crud.create_store(
            db, vector_store_create(name="find-me", embedding_model_id=model.id)
        )

        found = crud.get_store(db, created.id)
        assert found is not None
        assert found.name == "find-me"

    def test_returns_none_when_not_found(self, test_db_with_crud):
        """Returns None when store not found."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]

        result = crud.get_store(db, 9999)
        assert result is None


class TestUpdateStore:
    """Tests for update_store()."""

    def test_updates_store_fields(self, test_db_with_crud, monkeypatch):
        """Updates store name and description."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]
        vector_store_update = ctx["VectorStoreUpdate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, vector_store_create(name="original", embedding_model_id=model.id)
        )

        updated = crud.update_store(
            db,
            store.id,
            vector_store_update(name="updated", description="New desc"),
        )

        assert updated.name == "updated"
        assert updated.description == "New desc"

    def test_returns_none_when_not_found(self, test_db_with_crud):
        """Returns None when store not found."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        vector_store_update = ctx["VectorStoreUpdate"]

        result = crud.update_store(db, 9999, vector_store_update(name="x"))
        assert result is None


class TestDeleteStore:
    """Tests for delete_store()."""

    def test_deletes_store(self, test_db_with_crud, monkeypatch):
        """Deletes store from database."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, vector_store_create(name="delete-me", embedding_model_id=model.id)
        )
        store_id = store.id

        result = crud.delete_store(db, store_id)

        assert result is True
        assert crud.get_store(db, store_id) is None

    def test_deletes_index_directory(self, test_db_with_crud, monkeypatch):
        """Deletes store's index directory."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, vector_store_create(name="with-dir", embedding_model_id=model.id)
        )
        index_path = store.index_path

        crud.delete_store(db, store.id)

        assert not os.path.exists(index_path)

    def test_returns_false_when_not_found(self, test_db_with_crud):
        """Returns False when store not found."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]

        result = crud.delete_store(db, 9999)
        assert result is False


class TestCreateDocument:
    """Tests for create_document()."""

    def test_creates_document(self, test_db_with_crud, monkeypatch):
        """Creates document linked to store."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, vector_store_create(name="doc-store", embedding_model_id=model.id)
        )

        doc = crud.create_document(db, ctx["DocumentCreate"](store_id=store.id, filename="test.pdf", file_type="pdf", file_size=2048, chunk_count=0))

        assert doc.id is not None
        assert doc.store_id == store.id
        assert doc.filename == "test.pdf"
        assert doc.file_size == 2048


class TestGetStoreDocuments:
    """Tests for get_store_documents()."""

    def test_returns_store_documents(self, test_db_with_crud, monkeypatch):
        """Returns all documents for a store."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, vector_store_create(name="docs-store", embedding_model_id=model.id)
        )

        crud.create_document(db, ctx["DocumentCreate"](store_id=store.id, filename="a.pdf", file_type="pdf", file_size=100, chunk_count=0))
        crud.create_document(db, ctx["DocumentCreate"](store_id=store.id, filename="b.txt", file_type="txt", file_size=200, chunk_count=0))

        docs = crud.get_documents(db, store.id)

        assert len(docs) == 2
        filenames = [d.filename for d in docs]
        assert "a.pdf" in filenames
        assert "b.txt" in filenames

    def test_returns_empty_for_store_without_docs(self, test_db_with_crud, monkeypatch):
        """Returns empty list for store with no documents."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        vector_store_create = ctx["VectorStoreCreate"]

        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, vector_store_create(name="empty-store", embedding_model_id=model.id)
        )

        docs = crud.get_documents(db, store.id)
        assert docs == []


class TestDeleteDocument:
    """Tests for delete_document()."""

    def test_deletes_existing_document(self, test_db_with_crud, monkeypatch):
        """Deletes document successfully."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, ctx["VectorStoreCreate"](name="test-store", embedding_model_id=model.id)
        )
        doc = crud.create_document(
            db, ctx["DocumentCreate"](
                store_id=store.id, filename="test.txt", 
                file_type="txt", file_size=100, chunk_count=5
            )
        )

        result = crud.delete_document(db, doc.id)

        assert result is True
        assert crud.get_document(db, doc.id) is None

    def test_returns_false_when_not_found(self, test_db_with_crud):
        """Returns False when document doesn't exist."""
        db = test_db_with_crud["db"]
        crud_module = test_db_with_crud["crud"]

        result = crud_module.delete_document(db, 999)
        assert result is False


class TestUpdateStoreStats:
    """Tests for update_store_stats()."""

    def test_updates_document_and_chunk_counts(self, test_db_with_crud, monkeypatch):
        """Updates store statistics based on documents."""
        ctx = test_db_with_crud
        crud = ctx["crud"]
        db = ctx["db"]
        model = ctx["model"]
        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, ctx["VectorStoreCreate"](name="stats-store", embedding_model_id=model.id)
        )

        # Create documents with different chunk counts
        crud.create_document(
            db, ctx["DocumentCreate"](
                store_id=store.id, filename="doc1.txt",
                file_type="txt", file_size=100, chunk_count=5
            )
        )
        crud.create_document(
            db, ctx["DocumentCreate"](
                store_id=store.id, filename="doc2.txt",
                file_type="txt", file_size=200, chunk_count=10
            )
        )

        crud.update_store_stats(db, store.id)

        updated_store = crud.get_store(db, store.id)
        assert updated_store.document_count == 2
        assert updated_store.chunk_count == 15

    def test_no_error_when_store_not_found(self, test_db_with_crud):
        """No error when store doesn't exist."""
        db = test_db_with_crud["db"]
        crud_module = test_db_with_crud["crud"]

        # Should not raise
        crud_module.update_store_stats(db, 999)


# ======= Template CRUD Tests =======
@pytest.fixture
def test_db_with_templates(test_db_with_crud, monkeypatch):
    """Extends test_db_with_crud with a store for template testing."""
    
    ctx = test_db_with_crud
    monkeypatch.setattr(ctx["crud"], "DATA_DIR", ctx["temp_dir"])
    
    store = ctx["crud"].create_store(
        ctx["db"],
        ctx["VectorStoreCreate"](name="template-store", embedding_model_id=ctx["model"].id)
    )
    
    ctx["store"] = store
    ctx["TemplateCreateIn"] = TemplateCreateIn
    ctx["TemplateUpdateIn"] = TemplateUpdateIn
    ctx["MessageBlock"] = MessageBlock
    ctx["TemplateType"] = TemplateType
    
    return ctx


class TestGetTemplatesByStore:
    """Tests for get_templates_by_store()."""

    def test_returns_active_templates_for_store(self, test_db_with_templates):
        """Returns all active templates for a store (including auto-seeded defaults)."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        store = ctx["store"]
        
        # Store already has 2 default templates auto-seeded on creation
        # Create two additional custom templates
        crud.create_template(db, ctx["TemplateCreateIn"](
            name="Template 1",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=store.id,
            messages=[ctx["MessageBlock"](role="system", content="Hello")]
        ))
        crud.create_template(db, ctx["TemplateCreateIn"](
            name="Template 2",
            template_type=ctx["TemplateType"].RETRIEVE_OR_RESPOND,
            store_id=store.id,
            messages=[ctx["MessageBlock"](role="user", content="{user_input}")]
        ))
        
        result = crud.get_templates_by_store(db, store.id)
        
        # 2 default templates + 2 custom templates = 4 total
        assert len(result) == 4

    def test_filters_by_template_type(self, test_db_with_templates):
        """Filters templates by type when specified."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        store = ctx["store"]
        
        crud.create_template(db, ctx["TemplateCreateIn"](
            name="Answer Template",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=store.id,
            messages=[ctx["MessageBlock"](role="system", content="Answer")]
        ))
        crud.create_template(db, ctx["TemplateCreateIn"](
            name="Retrieve Template",
            template_type=ctx["TemplateType"].RETRIEVE_OR_RESPOND,
            store_id=store.id,
            messages=[ctx["MessageBlock"](role="system", content="Retrieve")]
        ))
        
        result = crud.get_templates_by_store(db, store.id, template_type="generate_answer")
        
        # 1 default + 1 custom generate_answer template = 2
        assert len(result) == 2
        assert all(t.template_type == "generate_answer" for t in result)

    def test_default_templates_seeded_on_store_creation(self, test_db_with_templates):
        """Verifies that default templates are auto-seeded when a store is created."""
        ctx = test_db_with_templates
        result = ctx["crud"].get_templates_by_store(ctx["db"], ctx["store"].id)
        
        # Should have 2 default templates: retrieve_or_respond and generate_answer
        assert len(result) == 2
        template_types = {t.template_type for t in result}
        assert template_types == {"retrieve_or_respond", "generate_answer"}


class TestGetTemplate:
    """Tests for get_template()."""

    def test_returns_template_by_id(self, test_db_with_templates):
        """Returns template when found by ID."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        
        created = crud.create_template(db, ctx["TemplateCreateIn"](
            name="My Template",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=ctx["store"].id,
            messages=[ctx["MessageBlock"](role="system", content="Hello")]
        ))
        
        result = crud.get_template(db, created.id)
        
        assert result is not None
        assert result.name == "My Template"
        assert result.id == created.id

    def test_returns_none_when_not_found(self, test_db_with_templates):
        """Returns None when template not found."""
        result = test_db_with_templates["crud"].get_template(
            test_db_with_templates["db"], 9999
        )
        assert result is None


class TestGetTemplateByStoreAndType:
    """Tests for get_template_by_store_and_type()."""

    def test_returns_template_matching_store_and_type(self, test_db_with_templates):
        """Returns template matching both store and type (returns first match, which is the default)."""
        ctx = test_db_with_templates
        db = ctx["db"]
        store = ctx["store"]
        
        # Default template for generate_answer is already seeded
        result = ctx["crud"].get_template_by_store_and_type(db, store.id, "generate_answer")
        
        assert result is not None
        assert result.template_type == "generate_answer"
        assert result.store_id == store.id

    def test_returns_none_when_not_found(self, test_db_with_templates):
        """Returns None when no matching template exists."""
        ctx = test_db_with_templates
        result = ctx["crud"].get_template_by_store_and_type(
            ctx["db"], ctx["store"].id, "nonexistent_type"
        )
        assert result is None


class TestCreateTemplate:
    """Tests for create_template()."""

    def test_creates_template_with_all_fields(self, test_db_with_templates):
        """Creates template with all required fields."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        store = ctx["store"]
        
        template = crud.create_template(db, ctx["TemplateCreateIn"](
            name="Full Template",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=store.id,
            messages=[
                ctx["MessageBlock"](role="system", content="System message"),
                ctx["MessageBlock"](role="user", content="{user_input}")
            ]
        ))
        
        assert template.id is not None
        assert template.name == "Full Template"
        assert template.template_type == "generate_answer"
        assert template.store_id == store.id
        assert template.is_active is True
        assert len(template.messages) == 2

    def test_raises_when_store_not_found(self, test_db_with_templates):
        """Raises ValueError when store doesn't exist."""
        ctx = test_db_with_templates
        
        with pytest.raises(ValueError, match="Store with id 9999 does not exist"):
            ctx["crud"].create_template(ctx["db"], ctx["TemplateCreateIn"](
                name="Orphan Template",
                template_type=ctx["TemplateType"].GENERATE_ANSWER,
                store_id=9999,
                messages=[ctx["MessageBlock"](role="system", content="Hello")]
            ))


class TestUpdateTemplate:
    """Tests for update_template()."""

    def test_updates_name(self, test_db_with_templates):
        """Updates template name."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        
        template = crud.create_template(db, ctx["TemplateCreateIn"](
            name="Original Name",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=ctx["store"].id,
            messages=[ctx["MessageBlock"](role="system", content="Hello")]
        ))
        
        updated = crud.update_template(db, template.id, ctx["TemplateUpdateIn"](
            name="Updated Name"
        ))
        
        assert updated.name == "Updated Name"

    def test_updates_messages(self, test_db_with_templates):
        """Updates template messages."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        
        template = crud.create_template(db, ctx["TemplateCreateIn"](
            name="Template",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=ctx["store"].id,
            messages=[ctx["MessageBlock"](role="system", content="Original")]
        ))
        
        updated = crud.update_template(db, template.id, ctx["TemplateUpdateIn"](
            messages=[
                ctx["MessageBlock"](role="system", content="Updated"),
                ctx["MessageBlock"](role="user", content="New message")
            ]
        ))
        
        assert len(updated.messages) == 2
        assert updated.messages[0]["content"] == "Updated"

    def test_updates_is_active(self, test_db_with_templates):
        """Updates template is_active status."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        
        template = crud.create_template(db, ctx["TemplateCreateIn"](
            name="Template",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=ctx["store"].id,
            messages=[ctx["MessageBlock"](role="system", content="Hello")]
        ))
        
        updated = crud.update_template(db, template.id, ctx["TemplateUpdateIn"](
            is_active=False
        ))
        
        assert updated.is_active is False

    def test_returns_none_when_not_found(self, test_db_with_templates):
        """Returns None when template not found."""
        ctx = test_db_with_templates
        result = ctx["crud"].update_template(
            ctx["db"], 9999, ctx["TemplateUpdateIn"](name="New Name")
        )
        assert result is None


class TestDeleteTemplate:
    """Tests for delete_template()."""

    def test_deletes_existing_template(self, test_db_with_templates):
        """Deletes template and returns True."""
        ctx = test_db_with_templates
        crud = ctx["crud"]
        db = ctx["db"]
        
        template = crud.create_template(db, ctx["TemplateCreateIn"](
            name="To Delete",
            template_type=ctx["TemplateType"].GENERATE_ANSWER,
            store_id=ctx["store"].id,
            messages=[ctx["MessageBlock"](role="system", content="Hello")]
        ))
        
        result = crud.delete_template(db, template.id)
        
        assert result is True
        assert crud.get_template(db, template.id) is None

    def test_returns_false_when_not_found(self, test_db_with_templates):
        """Returns False when template not found."""
        ctx = test_db_with_templates
        result = ctx["crud"].delete_template(ctx["db"], 9999)
        assert result is False
