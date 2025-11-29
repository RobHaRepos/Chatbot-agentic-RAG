import pytest
from anyio import lowlevel
from typing import Any, Coroutine, cast
from app.langgraph_code import wf_api

@pytest.mark.anyio
async def test_lifespan_context_manager(monkeypatch):
    """The lifespan context manager attaches and removes graph state on startup/shutdown."""
    class FakeGraph:
        def ainvoke(self, payload):
            # Intentionally left as a no-op for this unit test.
            # The real graph's `ainvoke` performs asynchronous workflow
            # execution and may call external services; here we only need
            # a lightweight placeholder so the lifespan context manager
            # can attach an object with the expected API to app.state.graph.
            # Keeping it empty avoids side-effects during unit tests.
            pass
        
    monkeypatch.setattr("app.langgraph_code.wf_api.build_workflow", lambda: FakeGraph())
    async with wf_api.lifespan(wf_api.app):
        assert wf_api.app.state.graph is not None
        assert isinstance(wf_api.app.state.graph, FakeGraph)
    
    assert getattr(wf_api.app.state, "graph", None) is None

def test_get_health_happy():
    """Health check returns an 'ok' dict for quick liveness check."""
    response = wf_api.health_check()
    assert isinstance(response, dict)
    assert response == {"status": "ok"}

def test_get_ready_happy(monkeypatch):
    """Ready check returns True when a graph is available in app.state."""
    monkeypatch.setattr("app.langgraph_code.wf_api.app.state.graph", object(), raising=False)
    response = wf_api.ready_check()
    assert isinstance(response, dict)
    assert "status" in response
    assert isinstance(response["status"], bool)
    assert response["status"] is True 
    
def test_get_ready_sad(monkeypatch):
    """Ready check returns False if no graph is attached to app.state."""
    monkeypatch.setattr("app.langgraph_code.wf_api.app.state.graph", None, raising=False)
    response = wf_api.ready_check()
    assert isinstance(response, dict)
    assert "status" in response
    assert isinstance(response["status"], bool)
    assert response["status"] is False 

@pytest.mark.anyio
async def test_run_workflow_happy(monkeypatch):
    """run_workflow calls graph.ainvoke and returns its result when present."""
    class FakeGraph:
        async def ainvoke(self, payload):
            await lowlevel.checkpoint()
            return {"result": "This is the answer!"}
    
    fake_graph = FakeGraph()
    monkeypatch.setattr("app.langgraph_code.wf_api.app.state.graph", fake_graph, raising=False)
    request = wf_api.RunRequest(question="What is the newest Iphone?", k=3, store_id=1)
    # cast to a Coroutine to satisfy static type checkers that this is awaitable
    result = await cast(Coroutine[Any, Any, dict[str, Any]], wf_api.run_workflow(request))
    assert isinstance(result, dict)
    assert "result" in result
    assert result["result"] == {"result": "This is the answer!"}

@pytest.mark.anyio
async def test_run_workflow_no_graph(monkeypatch):
    """run_workflow raises when app.state.graph is None."""
    monkeypatch.setattr("app.langgraph_code.wf_api.app.state.graph", None, raising=False)
    request = wf_api.RunRequest(question="Will this fail?", k=3, store_id=1)
    
    with pytest.raises(AttributeError):
        await cast(Coroutine[Any, Any, dict[str, Any]], wf_api.run_workflow(request))

@pytest.mark.anyio
async def test_run_workflow_invoke_exception(monkeypatch):
    """run_workflow propagates exceptions raised by graph.ainvoke."""
    class BrokenGraph:
        def ainvoke(self, payload):
            raise RuntimeError("Graph invocation failed")
    monkeypatch.setattr("app.langgraph_code.wf_api.app.state.graph", BrokenGraph(), raising=False)
    request = wf_api.RunRequest(question="Will invoke error?", k=3, store_id=1)
    
    with pytest.raises(RuntimeError):
        await cast(Coroutine[Any, Any, dict[str, Any]], wf_api.run_workflow(request))
