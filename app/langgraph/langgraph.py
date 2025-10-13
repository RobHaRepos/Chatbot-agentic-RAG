from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from app.langgraph.nodes import (
    node_retrieve_list,
    node_retrieve_string,
    node_generate_answer,
    node_rewrite_question,
    node_query_or_respond,
)

def build_workflow(vector_store, ):
    wf = StateGraph(MessagesState)
    
    wf.add_node("generate_query_or_respond", node_query_or_respond)    
    wf.add_node("retrieve", ToolNode(node_retrieve_string, vector_store=vector_store))
    wf.add_node("rewrite_question", node_rewrite_question)
    wf.add_node("answer", node_generate_answer)

    wf.add_edge(START, "generate_query_or_respond")
    wf.add_conditional_edges("generate_query_or_respond",
        tools_condition,
        {"tools": "retrieve",
        END: END,
        }
    )
    
#    wf.add_conditional_edges(
#        "retrieve",
#        grade_documents, # A function that grades the retrieved documents
#    )
    
    wf.add_edge("generate_answer", END)
    wf.add_edge("rewrite_question", "generate_query_or_respond")
    
    graph = wf.compile()
    return graph