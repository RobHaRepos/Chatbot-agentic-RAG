from unittest.mock import Mock, patch

import httpx

from app.llm.src.template_manager import CachedTemplate, TemplateManager

RETRIEVER_SERVICE_URL = "http://localhost:8001"

class TestCachedTemplate:
    """Tests for CachedTemplate dataclass."""

    def test_create_cached_template(self):
        """CachedTemplate can be instantiated with all fields."""
        template = CachedTemplate(
            store_id=1,
            template_type="generate_answer",
            messages=[("system", "Hello"), ("user", "{user_input}")]
        )
        assert template.store_id == 1
        assert template.template_type == "generate_answer"
        assert len(template.messages) == 2
        assert template.messages[0] == ("system", "Hello")


class TestTemplateManager:
    """Tests for TemplateManager class."""

    def test_init_strips_trailing_slash(self):
        """TemplateManager removes trailing slash from URL."""
        manager = TemplateManager(f"{RETRIEVER_SERVICE_URL}/")
        assert manager.retriever_service_url == RETRIEVER_SERVICE_URL
        
    def test_init_keeps_url_without_trailing_slash(self):
        """TemplateManager keeps URL intact if no trailing slash."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        assert manager.retriever_service_url == RETRIEVER_SERVICE_URL

    def test_init_empty_cache(self):
        """TemplateManager starts with empty cache."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        assert manager._cache == {}

    def test_default_templates_exist(self):
        """DEFAULT_TEMPLATES contains expected template types."""
        assert "retrieve_or_respond" in TemplateManager.DEFAULT_TEMPLATES
        assert "generate_answer" in TemplateManager.DEFAULT_TEMPLATES
        
    def test_default_templates_structure(self):
        """DEFAULT_TEMPLATES have correct structure."""
        for template_type, messages in TemplateManager.DEFAULT_TEMPLATES.items():
            assert isinstance(messages, list)
            for role, content in messages:
                assert role in ("system", "user", "assistant")
                assert isinstance(content, str)


class TestGetTemplate:
    """Tests for TemplateManager.get_template method."""

    def test_returns_cached_template(self):
        """get_template returns cached template if exists."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        cached = CachedTemplate(
            store_id=1, 
            template_type="generate_answer",
            messages=[("system", "Cached content")]
        )
        manager._cache[(1, "generate_answer")] = cached
        
        result = manager.get_template(1, "generate_answer")
        assert result == [("system", "Cached content")]

    @patch.object(TemplateManager, "_fetch_template")
    def test_fetches_and_caches_template(self, mock_fetch):
        """get_template fetches from service and caches result."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        mock_fetch.return_value = CachedTemplate(
            store_id=1,
            template_type="generate_answer",
            messages=[("system", "Fetched content")]
        )
        
        result = manager.get_template(1, "generate_answer")
        
        assert result == [("system", "Fetched content")]
        assert (1, "generate_answer") in manager._cache
        mock_fetch.assert_called_once_with(1, "generate_answer")

    @patch.object(TemplateManager, "_fetch_template")
    def test_returns_default_when_fetch_fails(self, mock_fetch):
        """get_template returns default template when fetch returns None."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        mock_fetch.return_value = None
        
        result = manager.get_template(1, "retrieve_or_respond")
        
        assert result == TemplateManager.DEFAULT_TEMPLATES["retrieve_or_respond"]

    @patch.object(TemplateManager, "_fetch_template")
    def test_returns_empty_for_unknown_template_type(self, mock_fetch):
        """get_template returns empty list for unknown template type."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        mock_fetch.return_value = None
        
        result = manager.get_template(1, "unknown_type")
        
        assert result == []


class TestFetchTemplate:
    """Tests for TemplateManager._fetch_template method."""

    @patch("app.llm.src.template_manager.httpx.get")
    def test_fetch_template_success(self, mock_get):
        """_fetch_template successfully fetches and parses template."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = [{
            "id": 1,
            "name": "Test Template",
            "template_type": "generate_answer",
            "store_id": 1,
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "{user_input}"}
            ],
            "is_active": True
        }]
        mock_get.return_value = mock_response
        
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        result = manager._fetch_template(1, "generate_answer")
        
        assert result is not None
        assert result.store_id == 1
        assert result.template_type == "generate_answer"
        assert result.messages == [
            ("system", "You are helpful."),
            ("user", "{user_input}")
        ]
        mock_get.assert_called_once_with(
            f"{RETRIEVER_SERVICE_URL}/templates",
            params={"store_id": 1, "template_type": "generate_answer"},
            timeout=5.0
        )

    @patch("app.llm.src.template_manager.httpx.get")
    def test_fetch_template_empty_response(self, mock_get):
        """_fetch_template returns None when no templates found."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        result = manager._fetch_template(1, "generate_answer")
        
        assert result is None

    @patch("app.llm.src.template_manager.httpx.get")
    def test_fetch_template_http_error(self, mock_get):
        """_fetch_template returns None on HTTP error."""
        mock_get.side_effect = httpx.HTTPError("Connection failed")
        
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        result = manager._fetch_template(1, "generate_answer")
        
        assert result is None

    @patch("app.llm.src.template_manager.httpx.get")
    def test_fetch_template_timeout(self, mock_get):
        """_fetch_template returns None on timeout."""
        mock_get.side_effect = httpx.TimeoutException("Request timed out")
        
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        result = manager._fetch_template(1, "generate_answer")
        
        assert result is None


class TestInvalidateCache:
    """Tests for TemplateManager.invalidate_cache method."""

    def test_invalidate_entire_cache(self):
        """invalidate_cache clears entire cache when no args."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        manager._cache[(1, "generate_answer")] = CachedTemplate(1, "generate_answer", [])
        manager._cache[(2, "retrieve_or_respond")] = CachedTemplate(2, "retrieve_or_respond", [])
        
        manager.invalidate_cache()
        
        assert manager._cache == {}

    def test_invalidate_by_store_id(self):
        """invalidate_cache removes only templates for given store_id."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        manager._cache[(1, "generate_answer")] = CachedTemplate(1, "generate_answer", [])
        manager._cache[(1, "retrieve_or_respond")] = CachedTemplate(1, "retrieve_or_respond", [])
        manager._cache[(2, "generate_answer")] = CachedTemplate(2, "generate_answer", [])
        
        manager.invalidate_cache(store_id=1)
        
        assert (1, "generate_answer") not in manager._cache
        assert (1, "retrieve_or_respond") not in manager._cache
        assert (2, "generate_answer") in manager._cache

    def test_invalidate_by_template_type(self):
        """invalidate_cache removes only templates of given type."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        manager._cache[(1, "generate_answer")] = CachedTemplate(1, "generate_answer", [])
        manager._cache[(2, "generate_answer")] = CachedTemplate(2, "generate_answer", [])
        manager._cache[(1, "retrieve_or_respond")] = CachedTemplate(1, "retrieve_or_respond", [])
        
        manager.invalidate_cache(template_type="generate_answer")
        
        assert (1, "generate_answer") not in manager._cache
        assert (2, "generate_answer") not in manager._cache
        assert (1, "retrieve_or_respond") in manager._cache

    def test_invalidate_by_store_and_type(self):
        """invalidate_cache removes specific store+type combo."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        manager._cache[(1, "generate_answer")] = CachedTemplate(1, "generate_answer", [])
        manager._cache[(1, "retrieve_or_respond")] = CachedTemplate(1, "retrieve_or_respond", [])
        manager._cache[(2, "generate_answer")] = CachedTemplate(2, "generate_answer", [])
        
        manager.invalidate_cache(store_id=1, template_type="generate_answer")
        
        assert (1, "generate_answer") not in manager._cache
        assert (1, "retrieve_or_respond") in manager._cache
        assert (2, "generate_answer") in manager._cache

    def test_invalidate_nonexistent_key_no_error(self):
        """invalidate_cache handles non-existent keys gracefully."""
        manager = TemplateManager(RETRIEVER_SERVICE_URL)
        
        # Should not raise
        manager.invalidate_cache(store_id=999)
        manager.invalidate_cache(template_type="nonexistent")
