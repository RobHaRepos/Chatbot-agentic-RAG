from app.langgraph.nodes import RETRIEVER_API_URL
from langchain_core.tools import tool
from app.langgraph.nodes import (
    node_retrieve_list,
    node_retrieve_string,
)

def get_tools():
    @tool
    def retrieve_list(query:str):
        """Retrieve a list of documents based on the query.

        Args:
            query (str): The search query.
        """
        return node_retrieve_list(query, k=5, retriever_url=RETRIEVER_API_URL)
    @tool
    def retrieve_string(query:str):
        """Retrieve a string of documents based on the query.

        Args:
            query (str): The search query.
        """
        return node_retrieve_string(query, k=5, retriever_url=RETRIEVER_API_URL)
    
    return [retrieve_string]
    