from app.langgraph_code.workflow import action_router, build_workflow
import pytest
from types import SimpleNamespace
from langgraph.graph import END

@pytest.fixture
def state_factory():
    """Helper to create OverallState-like SimpleNamespace objects."""
    def _create(action=None, **kwargs):
        payload = {
            "question": "",
            "action": action,
            "k": None,
            "context": None,
            "answer": None,
            "clarification": None,
        }
        payload.update(kwargs)
        return SimpleNamespace(**payload)
    return _create

def test_action_router_clarify(state_factory):
    overall_state = state_factory(action="clarify")
    action = action_router(overall_state)
    assert action == "clarify"
    
def test_action_router_answer(state_factory):
    overall_state = state_factory(action="answer")
    action = action_router(overall_state)
    assert action == "answer"

def test_action_router_retrieve(state_factory):
    overall_state = state_factory(action="retrieve")
    action = action_router(overall_state)
    assert action == "retrieve"
    
def test_action_router_no_action(state_factory):
    overall_state = state_factory()
    action = action_router(overall_state)
    assert action == END
    
def test_build_workflow():
    graph = build_workflow()
    assert graph is not None
    assert hasattr(graph, "invoke") and callable(graph.invoke)
    
    expected_nodes = {
        "generate_retrieve_or_respond",
        "retrieve",
        "answer",
        "clarify",
    }

    node_names = set(graph.nodes)
    assert expected_nodes.issubset(node_names)