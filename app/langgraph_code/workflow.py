from typing import Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from .nodes import (
    node_retrieve_string,
    node_generate_answer,
    node_retrieve_or_respond,
    node_ask_clarify
)

class OverallState(TypedDict):
    question: str
    query: str
    k: Optional[int]
    store_id: Optional[int]  # Vector store to query
    action: Optional[str]
    context: Optional[str]
    answer: Optional[str]
    clarification: Optional[str]
    documents: Optional[str]
    retrieval_counter: int
    

def action_router(state: OverallState):
    """Route based on the 'action' field in OverallState."""
    action = state.get("action") if isinstance(state, dict) else getattr(state, "action", None)

    if action == "clarify":
        return "clarify"
    elif action == "answer":
        return "answer"
    elif action == "retrieve":
        return "retrieve"
    
    return END


def initial_state(question: str, k: Optional[int] = None, store_id: Optional[int] = None) -> OverallState:
    """Create a fresh OverallState for each run of the workflow."""
    return {
        "question": question,
        "query": question,
        "k": k,
        "store_id": store_id,
        "action": None,
        "context": "",
        "answer": "",
        "clarification": None,
        "documents": "",
        "retrieval_counter": 0,
    }

def build_workflow():
    """Build the LangGraph workflow for the RAG chatbot."""
    wf = StateGraph(OverallState)

    wf.add_node("generate_retrieve_or_respond", node_retrieve_or_respond)
    wf.add_node("retrieve", node_retrieve_string)
    wf.add_node("answer", node_generate_answer)
    wf.add_node("clarify", node_ask_clarify)

    wf.add_edge(START, "generate_retrieve_or_respond")
    wf.add_conditional_edges("generate_retrieve_or_respond", 
                             action_router,{
                                "retrieve": "retrieve",
                                "clarify": "clarify",
                            })
    
    wf.add_edge("retrieve", "answer")
    wf.add_conditional_edges("answer",
                            action_router,{
                                "retrieve": "retrieve",
                                "clarify": "clarify",
                                END: END,
                        })

    wf.add_edge("clarify", END)
    
    graph = wf.compile()
    return graph