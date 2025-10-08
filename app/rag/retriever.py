from langchain.tools.retriever import create_retriever_tool
from app.config import NUMBER_OF_DOCUMENTS_TO_RETRIEVE as k

def create_retriever_tool_from_vectorstore(vector_store):
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
    
    retriever_tool = create_retriever_tool(
        retriever,
        name="faiss_retriever",
        description="Useful for when you need to answer questions about your documents.",
        )
    
    return retriever_tool

def retrieve_documents_as_string(query: str, retriever_tool) -> str:
    if retriever_tool is None:
        return ""
    docs = retriever_tool.run(query)
    return docs

def create_retriever_from_vectorstore(vector_store, k_search: int = k):
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k_search})
    return retriever

def retrieve_documents_as_list(query:str, retriever) -> list:
    if retriever is None:
        return []
    docs = retriever.invoke(query)
    return docs