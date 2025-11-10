from app.langgraph_code.workflow import decision_router, build_workflow
import pytest
from types import SimpleNamespace
from langgraph.graph import END

@pytest.fixture
def state_factory():
    """Helper to create OverallState-like SimpleNamespace objects."""
    def _create(decision=None, **kwargs):
        payload = {
            "question": "",
            "decision": decision,
            "k": None,
            "action": None,
            "context": None,
            "answer": None,
            "clarification": None,
        }
        payload.update(kwargs)
        return SimpleNamespace(**payload)
    return _create

def test_decision_router_clarify(state_factory):
    overall_state = state_factory(decision="clarify")
    decision = decision_router(overall_state)
    assert decision == "clarify"
    
def test_decision_router_answer(state_factory):
    overall_state = state_factory(decision="answer")
    decision = decision_router(overall_state)
    assert decision == "answer"

def test_decision_router_retrieve(state_factory):
    overall_state = state_factory(decision="retrieve")
    decision = decision_router(overall_state)
    assert decision == "retrieve"
    
def test_decision_router_no_decision(state_factory):
    overall_state = state_factory()
    decision = decision_router(overall_state)
    assert decision == END
    
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