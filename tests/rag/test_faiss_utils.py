"""Tests for FAISS utilities in faiss_utils.py."""
import pytest
import os
import tempfile
import shutil
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.rag.src import faiss_utils, crud, schemas
from app.rag.src.database import Base, EmbeddingModel
from app.rag.src.constants import METADATA_SOURCE, METADATA_DOCUMENT_ID

# Enable async testing
pytest_plugins = ('pytest_asyncio',)

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = test_session_local()

    model = EmbeddingModel(
        name="test-model", display_name="Test", dimension=384, is_available=True
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    temp_dir = tempfile.mkdtemp()

    yield {"db": db, "model": model, "temp_dir": temp_dir}

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestGetStoreOr404:
    """Tests for get_store_or_404()."""

    def test_returns_store_when_found(self, test_db, monkeypatch):
        """Returns store when it exists."""
        ctx = test_db
        db = ctx["db"]
        model = ctx["model"]
        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])

        store = crud.create_store(
            db, schemas.VectorStoreCreate(name="test-store", embedding_model_id=model.id)
        )

        result = faiss_utils.get_store_or_404(db, int(store.id))  # type: ignore[arg-type]
        assert result.id == store.id  # type: ignore[comparison-overlap]

    def test_raises_404_when_not_found(self, test_db):
        """Raises HTTPException 404 when store doesn't exist."""
        db = test_db["db"]

        with pytest.raises(HTTPException) as exc_info:
            faiss_utils.get_store_or_404(db, 999)

        assert exc_info.value.status_code == 404


class TestRemoveIndexFiles:
    """Tests for remove_index_files()."""

    def test_removes_existing_index_files(self):
        """Removes FAISS index files when they exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create fake index files
            index_file = os.path.join(temp_dir, "index.faiss")
            pkl_file = os.path.join(temp_dir, "index.pkl")

            with open(index_file, "w") as f:
                f.write("fake")
            with open(pkl_file, "w") as f:
                f.write("fake")

            faiss_utils.remove_index_files(temp_dir)

            assert not os.path.exists(index_file)
            assert not os.path.exists(pkl_file)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_no_error_when_files_dont_exist(self):
        """No error when index files don't exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Should not raise error
            faiss_utils.remove_index_files(temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestCreateChunkMetadata:
    """Tests for create_chunk_metadata()."""

    def test_creates_valid_metadata(self):
        """Creates metadata with all required fields."""
        meta = faiss_utils.create_chunk_metadata("test.txt", 42, 5)

        assert meta[METADATA_SOURCE] == "test.txt"
        assert meta[METADATA_DOCUMENT_ID] == 42
        assert "chunk_id" in meta
        assert meta["chunk_index"] == 5


class TestFilterAndCollectChunks:
    """Tests for filter_and_collect_chunks()."""

    def test_filters_chunks_by_condition(self, monkeypatch):
        """Filters chunks based on filter function."""
        doc1 = SimpleNamespace(
            page_content="chunk1", metadata={METADATA_DOCUMENT_ID: 1}
        )
        doc2 = SimpleNamespace(
            page_content="chunk2", metadata={METADATA_DOCUMENT_ID: 2}
        )
        fake_index = SimpleNamespace(docstore=SimpleNamespace(_dict={"a": doc1, "b": doc2}))

        chunks, metadatas = faiss_utils.filter_and_collect_chunks(
            fake_index, lambda doc: doc.metadata.get(METADATA_DOCUMENT_ID) == 1  # type: ignore[arg-type]
        )

        assert len(chunks) == 1
        assert chunks[0] == "chunk1"
        assert metadatas[0][METADATA_DOCUMENT_ID] == 1

    def test_returns_empty_when_index_is_none(self):
        """Returns empty lists when index is None."""
        chunks, metadatas = faiss_utils.filter_and_collect_chunks(
            None, lambda doc: True
        )

        assert chunks == []
        assert metadatas == []

    def test_applies_transform_function(self):
        """Applies transform function to matching docs."""
        doc1 = SimpleNamespace(
            page_content="chunk1", metadata={METADATA_SOURCE: "old.txt"}
        )
        fake_index = SimpleNamespace(docstore=SimpleNamespace(_dict={"a": doc1}))

        def transform(doc):
            doc.metadata[METADATA_SOURCE] = "new.txt"

        _, metadatas = faiss_utils.filter_and_collect_chunks(
            fake_index, lambda doc: True, transform_fn=transform  # type: ignore[arg-type]
        )

        assert metadatas[0][METADATA_SOURCE] == "new.txt"


class TestValidateDocumentOwnership:
    """Tests for validate_document_ownership()."""

    def test_raises_404_when_doc_is_none(self):
        """Raises 404 when document doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            faiss_utils.validate_document_ownership(None, 1, 1)

        assert exc_info.value.status_code == 404

    def test_raises_404_when_store_mismatch(self):
        """Raises 404 when document belongs to different store."""
        fake_doc = SimpleNamespace(store_id=5)

        with pytest.raises(HTTPException) as exc_info:
            faiss_utils.validate_document_ownership(fake_doc, 1, 10)

        assert exc_info.value.status_code == 404

    def test_no_error_when_valid(self):
        """No error when document exists and belongs to correct store."""
        fake_doc = SimpleNamespace(store_id=5)

        # Should not raise
        faiss_utils.validate_document_ownership(fake_doc, 1, 5)


class TestValidateUploadFile:
    """Tests for validate_upload_file()."""

    def test_accepts_txt_files(self):
        """Accepts .txt files."""
        file = Mock(spec=UploadFile, filename="test.txt")
        # Should not raise
        faiss_utils.validate_upload_file(file)

    def test_rejects_unsupported_extensions(self):
        """Rejects files with unsupported extensions."""
        file = Mock(spec=UploadFile, filename="test.pdf")

        with pytest.raises(HTTPException) as exc_info:
            faiss_utils.validate_upload_file(file)

        assert exc_info.value.status_code == 400
        assert "supported" in exc_info.value.detail.lower()

    def test_rejects_files_without_extension(self):
        """Rejects files without filename."""
        file = Mock(spec=UploadFile, filename=None)

        with pytest.raises(HTTPException) as exc_info:
            faiss_utils.validate_upload_file(file)

        assert exc_info.value.status_code == 400


class TestReadAndDecodeFile:
    """Tests for read_and_decode_file()."""

    @pytest.mark.asyncio
    async def test_reads_valid_utf8_file(self):
        """Reads and decodes valid UTF-8 file."""
        content = b"Hello world"
        file = AsyncMock(spec=UploadFile, filename="test.txt")
        file.read.return_value = content

        result_bytes, result_text = await faiss_utils.read_and_decode_file(file)

        assert result_bytes == content
        assert result_text == "Hello world"

    @pytest.mark.asyncio
    async def test_raises_400_on_decode_error(self):
        """Raises 400 when file is not valid UTF-8."""
        invalid_content = b"\xff\xfe"
        file = AsyncMock(spec=UploadFile, filename="test.txt")
        file.read.return_value = invalid_content

        with pytest.raises(HTTPException) as exc_info:
            await faiss_utils.read_and_decode_file(file)

        assert exc_info.value.status_code == 400
        assert "utf-8" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raises_400_on_empty_file(self):
        """Raises 400 when file is empty."""
        file = AsyncMock(spec=UploadFile, filename="empty.txt")
        file.read.return_value = b"   \n  "

        with pytest.raises(HTTPException) as exc_info:
            await faiss_utils.read_and_decode_file(file)

        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()


class TestSaveAndInvalidateIndex:
    """Tests for save_and_invalidate_index()."""

    def test_saves_and_invalidates_cache(self, monkeypatch):
        """Saves index and removes from cache."""
        faiss_utils.loaded_stores[1] = SimpleNamespace()  # type: ignore
        
        fake_index = Mock()
        temp_dir = tempfile.mkdtemp()
        
        try:
            faiss_utils.save_and_invalidate_index(fake_index, temp_dir, 1)
            
            fake_index.save_local.assert_called_once_with(temp_dir)
            assert 1 not in faiss_utils.loaded_stores
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestRebuildIndexWithNewContent:
    """Tests for rebuild_index_with_new_content()."""

    def test_rebuilds_index_with_new_chunks(self, monkeypatch):
        """Rebuilds index replacing old document chunks with new ones."""
        # Create fake index with existing chunks
        old_chunk = SimpleNamespace(
            page_content="old content",
            metadata={"document_id": 1, "source": "old.txt"}
        )
        keep_chunk = SimpleNamespace(
            page_content="keep this",
            metadata={"document_id": 2, "source": "keep.txt"}
        )
        fake_docstore = SimpleNamespace(_dict={"a": old_chunk, "b": keep_chunk})
        fake_index = SimpleNamespace(docstore=fake_docstore)
        
        fake_new_index = Mock()
        monkeypatch.setattr(
            faiss_utils.FAISS, "from_texts", lambda texts, emb, metadatas: fake_new_index
        )
        
        mock_embeddings = SimpleNamespace()
        new_index, chunk_count = faiss_utils.rebuild_index_with_new_content(
            fake_index, 1, "New content here", "new.txt", mock_embeddings  # type: ignore[arg-type]
        )
        
        assert new_index is fake_new_index
        assert chunk_count >= 1  # At least one chunk created

    def test_handles_none_index(self, monkeypatch):
        """Handles None index by creating new one."""
        fake_new_index = Mock()
        monkeypatch.setattr(
            faiss_utils.FAISS, "from_texts", lambda texts, emb, metadatas: fake_new_index
        )
        
        mock_embeddings = SimpleNamespace()
        new_index, chunk_count = faiss_utils.rebuild_index_with_new_content(
            None, 1, "Content", "file.txt", mock_embeddings
        )
        
        assert new_index is fake_new_index
        assert chunk_count >= 1


class TestUpdateIndexFilenames:
    """Tests for update_index_filenames()."""

    def test_updates_filename_metadata(self, monkeypatch):
        """Updates filename in metadata for specified document."""
        chunk1 = SimpleNamespace(
            page_content="chunk1",
            metadata={"document_id": 1, "source": "old.txt"}
        )
        chunk2 = SimpleNamespace(
            page_content="chunk2",
            metadata={"document_id": 2, "source": "other.txt"}
        )
        fake_docstore = SimpleNamespace(_dict={"a": chunk1, "b": chunk2})
        fake_index = SimpleNamespace(docstore=fake_docstore)
        
        fake_new_index = Mock()
        monkeypatch.setattr(
            faiss_utils.FAISS, "from_texts", lambda texts, emb, metadatas: fake_new_index
        )
        
        mock_embeddings = SimpleNamespace()
        new_index = faiss_utils.update_index_filenames(
            fake_index, 1, "renamed.txt", mock_embeddings  # type: ignore[arg-type]
        )
        
        assert new_index is fake_new_index
        # Verify the metadata was updated
        assert chunk1.metadata["source"] == "renamed.txt"
        assert chunk2.metadata["source"] == "other.txt"  # Unchanged


class TestProcessFileIntoChunks:
    """Tests for process_file_into_chunks()."""

    def test_processes_file_successfully(self, test_db, monkeypatch):
        """Processes file into chunks and creates document."""
        ctx = test_db
        db = ctx["db"]
        model = ctx["model"]
        
        monkeypatch.setattr(crud, "DATA_DIR", ctx["temp_dir"])
        
        from app.rag.src.schemas import VectorStoreCreate
        store = crud.create_store(
            db, VectorStoreCreate(name="test", embedding_model_id=model.id)
        )
        
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        
        file = Mock()
        file.filename = "test.txt"
        file.content_type = "text/plain"
        
        text = "This is a test file with some content that will be split into chunks."
        content = text.encode("utf-8")
        
        chunks, metadatas, doc = faiss_utils.process_file_into_chunks(
            file, text, content, int(store.id), splitter, db  # type: ignore[arg-type]
        )
        
        assert len(chunks) >= 1
        assert len(metadatas) == len(chunks)
        assert doc.filename == "test.txt"  # type: ignore[comparison-overlap]
        assert doc.file_size == len(content)  # type: ignore[comparison-overlap]
        assert doc.chunk_count == len(chunks)  # type: ignore[comparison-overlap]
