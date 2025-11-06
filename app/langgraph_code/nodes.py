import os
import httpx
from typing import Dict, Any
from workflow import OverallState

LLM_API_URL = os.environ.get("LANGGRAPH_LLM_API_URL", "http://localhost:8000")
RETRIEVER_API_URL = os.environ.get("LANGGRAPH_RETRIEVER_API_URL", "http://localhost:8001")

#def node_retrieve_list(query: str, k: int | None, retriever_url: str = RETRIEVER_API_URL) -> List[Dict]:
#    payload = {"query": query, "k": k}
#    r = httpx.post(f"{retriever_url}/retrieve_documents_list", json=payload, timeout=30.0)
#    r.raise_for_status()
#    body = r.json()
#    return body.get("documents", [])

async def node_retrieve_string(state: OverallState) -> Dict[str, Any]:
    payload = {"query": state["question"], "k": state["k"]}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{RETRIEVER_API_URL}/retrieve_documents_string", json=payload)
        r.raise_for_status()
        body = r.json()
        return {"action": "retrieve", "documents": body}

async def node_retrieve_or_respond(state: OverallState) -> Dict[str, Any]:
    payload = {"question": state["question"]}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{LLM_API_URL}/retrieve_or_respond", json=payload)
        r.raise_for_status()
        body = r.json()
        if not isinstance(body, dict) or "decision" not in body:
            txt = body if isinstance(body, str) else str(body)
            return {"decision": "clarify", "answer": txt}
    return body

async def node_generate_answer(state: OverallState) -> Dict[str, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{LLM_API_URL}/generate_answer", json={"prompt": f"CONTEXT: \n{state['context']}\n\nQUESTION: {state['question']}"})
        r.raise_for_status()
        return {"action": "answer", "answer": r.json().get("answer", "")}

#def node_rewrite_question(question: str, context: str, llm_api_url: str = LLM_API_URL) -> str:
#    r = httpx.post(f"{llm_api_url}/generate_search_query", json={"question": question, "context": context}, timeout=30.0)
#    r.raise_for_status()
#    return r.json().get("query", "")

async def node_ask_clarify(state: OverallState) -> Dict[str, str]:
    """Return a short clarification prompt to the user."""
    return {"action": "clarify", "message": "Could you be more specific? Which phone model or what detail do you mean (brand/model/specs/price)?"}
    