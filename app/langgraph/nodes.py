import httpx
from typing import List, Dict, Any

LLM_API_URL = "http://localhost:8000" # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
RETRIEVER_API_URL = "http://localhost:8001" # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def node_retrieve_list(query: str, k: int | None, retriever_url: str = RETRIEVER_API_URL) -> List[Dict]:
    payload = {"query": query, "k": k}
    r = httpx.post(f"{retriever_url}/retrieve_documents_list", json=payload, timeout=30.0)
    r.raise_for_status()
    body = r.json()
    return body.get("documents", [])

def node_retrieve_string(query: str, k: int | None, retriever_url: str = RETRIEVER_API_URL) -> str:
    payload = {"query": query, "k": k}
    r = httpx.post(f"{retriever_url}/retrieve_documents_string", json=payload, timeout=30.0)
    r.raise_for_status()
    body = r.json()
    return body.get("documents", "")

def node_retrieve_or_respond(question: str) -> Dict[str, Any]:
    payload = {"question": question}
    r = httpx.post(f"{LLM_API_URL}/retrieve_or_respond", json=payload, timeout=30.0)
    r.raise_for_status()
    body = r.json()
    if not isinstance(body, dict) or "decision" not in body:
        txt = body if isinstance(body, str) else str(body)
        return {"decision": "clarify", "answer": txt}
    return body

def node_generate_answer(question: str, retrieve: List[Dict], llm_api_url: str = LLM_API_URL) -> str:
    context = "\n\n".join(d.get("text") or d.get("page_content") for d in [retrieve or []])
    r = httpx.post(f"{llm_api_url}/generate_answer", json={"prompt": f"CONTEXT: \n{context}\n\nQUESTION: {question}"}, timeout=30.0)
    r.raise_for_status()
    return r.json().get("text", "")

def node_rewrite_question(question: str, retrieve: List[Dict], llm_api_url: str = LLM_API_URL) -> str:
    snippets = "\n\n".join(d.get("text") or d.get("page_content") for d in [retrieve or []])
    r = httpx.post(f"{llm_api_url}/generate_search_query", json={"question": question, "context": snippets}, timeout=30.0)
    r.raise_for_status()
    return r.json().get("query", "")

def node_ask_clarify(question: str) -> Dict[str, str]:
    """Return a short clarification prompt to the user."""
    return {"action": "clarify", "message": "Could you be more specific? Which phone model or what detail do you mean (brand/model/specs/price)?"}
    