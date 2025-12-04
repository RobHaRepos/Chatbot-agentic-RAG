import pytest
import requests

from tests.retriever.test_retriever import _service_up, BASE_URL


pytestmark = pytest.mark.skipif(
    not _service_up(BASE_URL),
    reason="Retriever service is not running"
)

class TestHealthIntegration:
    """Integration tests for health endpoint."""
    def test_health_returns_ok(self):
        """Health endpoint returns 200 with status ok."""
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

class TestEmbeddingModelsIntegration:
    """Integration tests for embedding models endpoint."""
    def test_list_embedding_models(self):
        """GET /embedding-models returns seeded models."""
        resp = requests.get(f"{BASE_URL}/embedding-models", timeout=5)
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) >= 2  # Seeded models
        names = [m["name"] for m in models]
        assert "all-MiniLM-L6-v2" in names
        assert "all-mpnet-base-v2" in names

class TestStoresCRUDIntegration:
    """Integration tests for stores CRUD endpoints."""
    def test_list_stores(self):
        """GET /stores returns list of stores."""
        resp = requests.get(f"{BASE_URL}/stores", timeout=5)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_get_update_delete_store(self):
        """Full CRUD lifecycle for a store."""
        create_resp = requests.post(
            f"{BASE_URL}/stores",
            json={
                "name": "integration-test-store",
                "description": "Created by integration test",
                "embedding_model_id": 1,
            },
            timeout=5,
        )
        assert create_resp.status_code == 201
        store = create_resp.json()
        store_id = store["id"]
        assert store["name"] == "integration-test-store"

        try:
            get_resp = requests.get(f"{BASE_URL}/stores/{store_id}", timeout=5)
            assert get_resp.status_code == 200
            assert get_resp.json()["id"] == store_id

            update_resp = requests.patch(
                f"{BASE_URL}/stores/{store_id}",
                json={"name": "updated-integration-store", "description": "Updated"},
                timeout=5,
            )
            assert update_resp.status_code == 200
            assert update_resp.json()["name"] == "updated-integration-store"

        finally:
            delete_resp = requests.delete(f"{BASE_URL}/stores/{store_id}", timeout=5)
            assert delete_resp.status_code == 204

    def test_get_store_not_found(self):
        """GET /stores/{id} returns 404 for non-existent store."""
        resp = requests.get(f"{BASE_URL}/stores/99999", timeout=5)
        assert resp.status_code == 404

    def test_create_store_invalid_data(self):
        """POST /stores returns 422 for invalid data."""
        resp = requests.post(
            f"{BASE_URL}/stores",
            json={"name": "", "embedding_model_id": 1},
            timeout=5,
        )
        assert resp.status_code == 422

class TestRetrievalIntegration:
    """Integration tests for retrieval endpoints."""
    def test_retrieve_from_nonexistent_store(self):
        """POST /stores/{id}/retrieve returns 404 for non-existent store."""
        resp = requests.post(
            f"{BASE_URL}/stores/99999/retrieve",
            json={"query": "test query", "k": 5},
            timeout=5,
        )
        assert resp.status_code == 404

    def test_retrieve_string_from_nonexistent_store(self):
        """POST /stores/retrieve_string returns 404 for non-existent store."""
        resp = requests.post(
            f"{BASE_URL}/stores/retrieve_string",
            params={"store_id": 99999},
            json={"query": "test query", "k": 5},
            timeout=5,
        )
        assert resp.status_code == 404