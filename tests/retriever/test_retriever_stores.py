"""Tests for store index management functions in retriever module."""
from types import SimpleNamespace
import app.retriever.src.retriever as retriever_module
from app.retriever.src import faiss_utils


class TestGetStoreIndex:
    """Tests for get_store_index() caching logic."""

    def test_loads_index_when_not_cached(self, monkeypatch):
        """First call loads index and caches it."""
        faiss_utils.loaded_stores.clear()

        fake_index = SimpleNamespace(similarity_search_with_score=lambda q, k: [])
        monkeypatch.setattr(
            retriever_module.FAISS,
            "load_local",
            lambda path, emb, allow_dangerous_deserialization: fake_index,
        )
        monkeypatch.setattr(retriever_module, "embeddings", SimpleNamespace(), raising=False)
        # Mock os.path.exists to return True so index loading is attempted
        monkeypatch.setattr("os.path.exists", lambda path: True)
        mock_embeddings = SimpleNamespace()

        result = retriever_module.get_store_index(1, "fake/path", mock_embeddings)

        assert result is fake_index
        assert 1 in faiss_utils.loaded_stores

    def test_returns_cached_index(self, monkeypatch):
        """Second call returns cached index without loading."""
        cached_index = SimpleNamespace(name="cached")
        # Type ignore for test - we're using SimpleNamespace as mock
        faiss_utils.loaded_stores[99] = cached_index  # type: ignore

        load_called = []
        monkeypatch.setattr(
            retriever_module.FAISS,
            "load_local",
            lambda *a, **k: load_called.append(1),
        )
        mock_embeddings = SimpleNamespace()

        result = retriever_module.get_store_index(99, "any/path", mock_embeddings)

        assert result is cached_index
        assert load_called == []  # load_local not called

    def test_different_stores_cached_separately(self, monkeypatch):
        """Each store ID has its own cached index."""
        faiss_utils.loaded_stores.clear()

        call_count = [0]

        def fake_load(path, emb, allow_dangerous_deserialization):
            call_count[0] += 1
            return SimpleNamespace(id=call_count[0])

        monkeypatch.setattr(retriever_module.FAISS, "load_local", fake_load)
        monkeypatch.setattr(retriever_module, "embeddings", SimpleNamespace(), raising=False)
        # Mock os.path.exists to return True so index loading is attempted
        monkeypatch.setattr("os.path.exists", lambda path: True)
        mock_embeddings = SimpleNamespace()

        idx1 = retriever_module.get_store_index(1, "path1", mock_embeddings)
        idx2 = retriever_module.get_store_index(2, "path2", mock_embeddings)

        assert getattr(idx1, "id") == 1
        assert getattr(idx2, "id") == 2
        assert len(faiss_utils.loaded_stores) == 2


class TestInvalidateStoreIndex:
    """Tests for invalidate_store_index()."""

    def test_removes_cached_store(self):
        """Invalidating removes store from cache."""
        faiss_utils.loaded_stores[5] = SimpleNamespace()  # type: ignore

        retriever_module.invalidate_store_index(5)

        assert 5 not in faiss_utils.loaded_stores

    def test_no_error_if_not_cached(self):
        """Invalidating non-existent store doesn't raise."""
        faiss_utils.loaded_stores.pop(999, None)

        retriever_module.invalidate_store_index(999)  # Should not raise
