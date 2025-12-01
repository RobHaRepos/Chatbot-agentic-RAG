import pytest
from app.logger_service.handlers import HTTPLogHandler as _HTTPLogHandler
from anyio import lowlevel
from typing import cast, Any
import logging
from app.langgraph_code.workflow import OverallState
from app.langgraph_code.nodes import (
    node_retrieve_string,
    node_generate_answer,
    node_retrieve_or_respond,
    node_ask_clarify,
)

@pytest.fixture
def state_factory():
    def _create(question: str, k: int = 3, store_id: int = 1, **kwargs) -> OverallState:
        payload: dict[str, Any] = {
            "question": question,
            "query": question,
            "k": k,
            "store_id": store_id,
            "action": None,
            "context": None,
            "answer": None,
            "clarification": None,
            "documents": None,
            "retrieval_counter": 0,
        }
        payload.update(kwargs)
        return cast(OverallState, payload)
    return _create

class FakeResponse:
    def __init__(self, data):
        self._data = data
    def raise_for_status(self):
        return None
    def json(self):
        return self._data

class FakeAsyncClient:
    def __init__(self, response):
        self._response = response
        self.last_request = None
        
    async def post(self, url, json):
        await lowlevel.checkpoint()
        self.last_request = (url, json)
        return self._response
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        return False

@pytest.mark.anyio
async def test_node_retrieve_string(monkeypatch, state_factory):
    """node_retrieve_string fetches and returns documents text from retriever service."""
    fake_response = FakeResponse({"documents": "DOC_A\n\nDOC_B"})
    
    fake_client = FakeAsyncClient(fake_response)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)
    
    state = state_factory(
        question="What is the newest Iphone?",
        query="What is the newest Iphone?",
        k=3,
        store_id=1
    )
        
    result = await node_retrieve_string(state)
    assert isinstance(result, dict)
    assert "documents" in result

    docs_text = result["documents"]
    assert "DOC_A" in docs_text
    assert "DOC_B" in docs_text

@pytest.mark.anyio
async def test_node_retrieve_string_no_store_id(state_factory):
    """node_retrieve_string returns clarify action when no store_id is provided."""
    state = state_factory(
        question="What is the newest Iphone?",
        query="What is the newest Iphone?",
        k=3,
        store_id=None  # No store_id
    )
        
    result = await node_retrieve_string(state)
    assert isinstance(result, dict)
    assert result["action"] == "clarify"
    assert result["documents"] == ""
        
@pytest.mark.anyio
async def test_node_retrieve_or_respond_retrieve(monkeypatch, state_factory):
    """retrieve_or_respond returns retrieve action when LLM indicates retrieval is needed."""
    fake_response_retrieve = FakeResponse({"action": "retrieve", "answer": ""})
    fake_client = FakeAsyncClient(fake_response_retrieve)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the newest Iphone?"
    )
    
    result = await node_retrieve_or_respond(state)
    assert isinstance(result, dict)
    assert "action" in result
    assert result["action"] == "retrieve"
    assert "answer" in result

@pytest.mark.anyio
async def test_node_retrieve_or_respond_clarify(monkeypatch, state_factory):
    """retrieve_or_respond returns clarify action on empty/insufficient question."""
    fake_response_clarify = FakeResponse({"action": "clarify", "answer": ""})
    fake_client = FakeAsyncClient(fake_response_clarify)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the capital of France?"
    )
    
    result = await node_retrieve_or_respond(state)
    assert isinstance(result, dict)
    assert "action" in result
    assert result["action"] == "clarify"
    
@pytest.mark.anyio
async def test_node_retrieve_or_respond_fallback(monkeypatch, state_factory):
    """retrieve_or_respond falls back to clarify when the LLM returns non-JSON."""
    fake_response_fallback = FakeResponse("Non-JSON response")
    fake_client = FakeAsyncClient(fake_response_fallback)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the newest Iphone?"
    )
    
    result = await node_retrieve_or_respond(state)
    assert isinstance(result, dict)
    assert "action" in result
    assert result["action"] == "clarify"    
    
@pytest.mark.anyio
class TestNodeGenerateAnswer:
    async def test_generate_answer(self, monkeypatch, state_factory):
        """Test generate_answer with normal input."""
        fake_response1 = FakeResponse("The newest Iphone is Iphone 15 with a new A17 chip.")
        fake_client1 = FakeAsyncClient(fake_response1)
        monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client1)

        state = state_factory(
            question="What is the newest Iphone?",
            documents="Iphone 15 was released in September 2023.",
            context="It has a new A17 chip."
        )
        result = await node_generate_answer(state)
        assert isinstance(result, dict)
        assert "answer" in result
        assert "Iphone 15" in result["answer"]
        assert "A17 chip" in result["answer"]
        
    async def test_generate_retrieve(self, monkeypatch, state_factory):
        """Test generate_answer leading to retrieve action."""
        fake_response2 = FakeResponse({"action":"retrieve","query":"Display of the Iphone 13", "context": "Newest Iphone is Iphone 13, Released 2022"})
        fake_client2 = FakeAsyncClient(fake_response2)
        monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client2)
        
        state = state_factory(
            question="What is the newest Iphone?",
            documents="The Iphone has a big display.",
            context="",
            retrieval_counter=0
        )
        result = await node_generate_answer(state)
        print(result, type(result))
        assert isinstance(result, dict)
        assert "action" in result
        assert result["action"] == "retrieve"
        assert "query" in result
        assert result["query"] == "Display of the Iphone 13"
        assert "context" in result
        assert result["context"] == "Newest Iphone is Iphone 13, Released 2022"
        
        
    async def test_generate_clarify(self, monkeypatch, state_factory):    
        """Test generate_answer leading to clarify action."""
        # state of retriever_counter = 3
        fake_response6 = FakeResponse({"action":"retrieve","query":"Display of the Iphone 13", "context": "Newest Iphone is Iphone 13, Released 2022"})
        fake_client6 = FakeAsyncClient(fake_response6)
        monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client6)

        state = state_factory(
            question="What is the newest Iphone?",
            documents="It has a big display",
            context="",
            retrieval_counter=5
        )
        result = await node_generate_answer(state)
        print(result, type(result))
        assert isinstance(result, dict)
        assert "action" in result
        assert result["action"] == "clarify"
        assert 'answer' in result

def test_node_ask_clarify(state_factory):
    """Test node_ask_clarify function."""
    state = state_factory(
        question="What is the capital of France?"
    )

    result = node_ask_clarify(state)
    assert isinstance(result, dict)
    assert "answer" in result
    assert "The query seems to be unrelated to phones. Could you be more specific? Which phone model or what detail do you mean (brand/model/specs/price)?" in result["answer"]
    assert "action" in result
    assert "clarify" in result["action"]


def test_nodes_attach_http_handler():
    """Loggers used by nodes should attach HTTPLogHandler so they forward to central logger."""
    logger = logging.getLogger("langgraph_nodes")
    handlers = [h for h in logger.handlers if h.__class__.__name__ == "HTTPLogHandler"]
    assert handlers, "langgraph_nodes must attach HTTPLogHandler"

    h = cast(_HTTPLogHandler, handlers[0])
    try:
        if hasattr(h, "_stopped"):
            getattr(h, "_stopped").set()
        if hasattr(h, "_worker"):
            getattr(h, "_worker").join(timeout=1)
    except Exception:
        pass