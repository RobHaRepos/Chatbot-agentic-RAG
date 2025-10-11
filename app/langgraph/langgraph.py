from typing import Optional, Callable
from app.rag.retriever import create_retriever_from_vectorstore, retrieve_documents_as_list
from app.config import NUMBER_OF_DOCUMENTS_TO_RETRIEVE as k
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode

def retriever_node(vector_store, query:str, k_override: Optional[int] = None) -> list:
    retriever = create_retriever_from_vectorstore(vector_store, k_search=k_override if k_override else k)
    return retrieve_documents_as_list(query, retriever)

def build_workflow(vector_store, ):
    wf = StateGraph(MessagesState)
    
    wf.add_node("generate_query_or_respond", )    
    wf.add_node("retrieve", ToolNode([retriever_node]))
    wf.add_node("rewrite_question", )
    wf.add_node("answer", )
    
    wf.add_edge(START, "generate_query_or_respond")
    wf.add_conditional_edges("generate_query_or_respond",
        tools_condition,
        {"tools": "retrieve",
        END: END,
        }
    )
    
    wf.add_conditional_edges(
        "retrieve",
        grade_documents, # A function that grades the retrieved documents
    )
    what do I do with this 
    It this doing it right?
    
    wf.add_edge("generate_answer", END)
    wf.add_edge("rewrite_question", "generate_query_or_respond")
    
    graph = wf.compile()
    return graph