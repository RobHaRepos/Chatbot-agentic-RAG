import pytest
from typing import cast, Any
from app.langgraph_code.workflow import OverallState
from app.langgraph_code.nodes import (
    node_retrieve_string,
    node_generate_answer,
    node_retrieve_or_respond,
    node_ask_clarify,
)

@pytest.fixture
def state_factory():
    def _create(question: str, k: int = 3, **kwargs) -> OverallState:
        payload: dict[str, Any] = {
            "question": question,
            "decision": None,
            "k": k,
            "action": None,
            "context": None,
            "answer": None,
            "clarification": None,
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
        self.last_request = (url, json)
        return self._response
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        return False

@pytest.mark.anyio
async def test_node_retrieve_string(monkeypatch, state_factory):
    fake_response = FakeResponse({"documents": "DOC_A\n\nDOC_B"})
    
    fake_client = FakeAsyncClient(fake_response)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)
    
    state = state_factory(
        question="What is the newest Iphone?",
        k=3
    )
        
    result = await node_retrieve_string(state)
    assert isinstance(result, dict)
    assert "documents" in result

    docs_text = result["context"]
    assert "DOC_A" in docs_text
    assert "DOC_B" in docs_text
        
@pytest.mark.anyio
async def test_node_retrieve_or_respond_retrieve(monkeypatch, state_factory):
    fake_response_retrieve = FakeResponse({"decision": "retrieve", "answer": ""})
    fake_client = FakeAsyncClient(fake_response_retrieve)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the newest Iphone?"
    )
    
    result = await node_retrieve_or_respond(state)
    assert isinstance(result, dict)
    assert "decision" in result
    assert result["decision"] == "retrieve"
    assert "answer" in result

@pytest.mark.anyio
async def test_node_retrieve_or_respond_clarify(monkeypatch, state_factory):
    fake_response_clarify = FakeResponse({"decision": "clarify", "answer": ""})
    fake_client = FakeAsyncClient(fake_response_clarify)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the capital of France?"
    )
    
    result = await node_retrieve_or_respond(state)
    assert isinstance(result, dict)
    assert "decision" in result
    assert result["decision"] == "clarify"
    assert "answer" in result
    
@pytest.mark.anyio
async def test_node_retrieve_or_respond_fallback(monkeypatch, state_factory):
    fake_response_fallback = FakeResponse("Non-JSON response")
    fake_client = FakeAsyncClient(fake_response_fallback)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the newest Iphone?"
    )
    
    result = await node_retrieve_or_respond(state)
    assert isinstance(result, dict)
    assert "decision" in result
    assert result["decision"] == "clarify"
    assert "answer" in result
    
@pytest.mark.anyio
async def test_node_generate_answer(monkeypatch, state_factory):
    fake_response = FakeResponse({"answer": "The newest Iphone is Iphone 15."})
    fake_client = FakeAsyncClient(fake_response)
    monkeypatch.setattr("app.langgraph_code.nodes.httpx.AsyncClient", lambda *args, **kwargs: fake_client)

    state = state_factory(
        question="What is the newest Iphone?",
        context="Iphone 15 was released in September 2023."
    )
    
    result = await node_generate_answer(state)
    assert isinstance(result, dict)
    assert "answer" in result
    assert "Iphone 15" in result["answer"]
    
def test_node_ask_clarify(state_factory):
    state = state_factory(
        question="What is the capital of France?"
    )

    result = node_ask_clarify(state)
    assert isinstance(result, dict)
    assert "answer" in result
    assert "The query seems to be unrelated to phones. Could you be more specific? Which phone model or what detail do you mean (brand/model/specs/price)?" in result["answer"]
    assert "action" in result
    assert "clarify" in result["action"]