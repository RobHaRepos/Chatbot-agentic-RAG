from typing import Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from nodes import (
    #node_retrieve_list,
    node_retrieve_string,
    node_generate_answer,
    #node_rewrite_question,
    node_retrieve_or_respond,
    node_ask_clarify
)

class OverallState(TypedDict):
    question: str
    decision: Optional[str]
    k: Optional[int]
    action: Optional[str]
    context: Optional[str]
    answer: Optional[str]
    clarification: Optional[str]
    documents: Optional[list[str]]

def decision_router(state: OverallState):
    # State is a dict-like mapping at runtime; use .get to read the decision reliably
    decision = state.get("decision") if isinstance(state, dict) else getattr(state, "decision", None)

    if decision == "clarify":
        return "clarify"
    elif decision == "answer":
        return "answer"
    elif decision == "retrieve":
        return "retrieve"
    
    return END

def build_workflow():
    wf = StateGraph(OverallState)

    # node name must match edges below — use 'generate_retrieve_or_respond'
    wf.add_node("generate_retrieve_or_respond", node_retrieve_or_respond)
    wf.add_node("retrieve", node_retrieve_string)
    #wf.add_node("rewrite_question", node_rewrite_question)
    wf.add_node("answer", node_generate_answer)
    wf.add_node("clarify", node_ask_clarify)

    wf.add_edge(START, "generate_retrieve_or_respond")
    wf.add_conditional_edges("generate_retrieve_or_respond", 
                             decision_router,{
                                "retrieve": "retrieve",
                                "clarify": "clarify",
                                "answer": "answer",
                                END: END,
                            })
    #Add edge: retrieve --> evaluate if enough info to answer --> answer or rewrite_question
    
    wf.add_edge("retrieve", "answer")
    wf.add_edge("answer", END)
    wf.add_edge("clarify", END)
    
    graph = wf.compile()
    return graph