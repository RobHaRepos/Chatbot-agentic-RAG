import logging
import os
from typing import TYPE_CHECKING, Any, Dict

import httpx

from app.logger_service.handlers import HTTPLogHandler

if TYPE_CHECKING:
    from .workflow import OverallState

LLM_API_URL = os.environ.get("LANGGRAPH_LLM_API_URL", "http://localhost:8002")
RETRIEVER_API_URL = os.environ.get("LANGGRAPH_RETRIEVER_API_URL", "http://localhost:8001")
MAX_RETRIEVES = int(os.environ.get("MAX_RETRIEVES", 4))
LOGGER_SERVICE_URL = os.environ.get("LOGGER_SERVICE_URL", "http://localhost:8004")

logger = logging.getLogger("langgraph_nodes")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
remote = HTTPLogHandler(LOGGER_SERVICE_URL)
logger.addHandler(remote)
logger.setLevel(logging.INFO)


async def node_retrieve_string(state: "OverallState") -> Dict[str, Any]:
    store_id = state.get("store_id")
    if not store_id:
        logger.error("node_retrieve_string: no store_id provided")
        return {"action": "clarify", "answer": "Vector store not found. Please select a store first."}
    
    payload = {"query": state["query"], "k": state.get("k")}
    url = f"{RETRIEVER_API_URL}/stores/retrieve_string?store_id={store_id}"
    logger.info("node_retrieve_string: sending to %s payload=%s", url, payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload)
        try:
            r.raise_for_status()
        except Exception:
            logger.exception("Retriever call failed; status=%s text=%s", getattr(r, 'status_code', None), getattr(r, 'text', None))
            raise
        body = r.json()
        
        logger.info("node_retrieve_string: got body keys=%s; length=%s", (list(body.keys()) if isinstance(body, dict) else type(body)), (len(str(body)) if body else 0))
        logger.info("node_retrieve_string: retrieved documents: %s", str(body))  # log the body
        state["action"] = "retrieve"
        state["documents"] = body.get("documents", "")
        return {"action": "retrieve", "documents": body.get("documents", "")}

async def node_retrieve_or_respond(state: "OverallState") -> Dict[str, Any]:  
    store_id = state.get("store_id")
    if not store_id:
        logger.error("node_retrieve_or_respond: no store_id provided")
        return {"action": "clarify", "answer": "No vector store selected. Please select a store first."}
    
    if state["question"] is None or state["question"].strip() == "":
        logger.info("node_retrieve_or_respond: empty user question, asking to clarify")
        return {"action": "clarify", "answer": "I'm sorry, but I need a question to provide an answer."}
    
    payload = {"question": state["question"], "store_id": store_id}
    logger.info("node_retrieve_or_respond: calling LLM %s with payload=%s", LLM_API_URL, payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{LLM_API_URL}/retrieve_or_respond", json=payload)
        r.raise_for_status()
        body = r.json()
        logger.info("node_retrieve_or_respond: LLM returned: %s", body)
        if "action" not in body:
            logger.info("node_retrieve_or_respond: asking to clarify")
            return {"action": "clarify", "answer": "Please clarify your question."}
    return body

async def node_generate_answer(state: "OverallState") -> Dict[str, Any]:
    store_id = state.get("store_id")
    if not store_id:
        logger.error("node_generate_answer: no store_id provided")
        return {"action": "clarify", "answer": "No vector store selected. Please select a store first."}
    
    payload = {
        "question": state["question"], 
        "documents": state.get("documents", ""), 
        "context": state.get("context", ""),
        "store_id": store_id
    }
    logger.info("node_generate_answer: calling LLM %s", LLM_API_URL)
    logger.info("node_generate_answer: payload keys: %s", list(payload.keys()))
    logger.info("node_generate_answer: payload content: %s", payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{LLM_API_URL}/generate_answer", json=payload)
        r.raise_for_status()
        resp = r.json()
        logger.info("node_generate_answer: LLM returned: %s", resp)
        logger.info("node_generate_answer: type of resp: %s", type(resp))
        
        if state.get("retrieval_counter") is None:
            state["retrieval_counter"] = 0
        elif state.get("retrieval_counter", 0) > MAX_RETRIEVES:
            logger.info("node_generate_answer: too many retrievals, asking to clarify")
            return {"action": "clarify", "answer": "Too many retrievals. Please clarify your question."}
        
        if "action" in resp and "retrieve" == resp.get("action", ""):
            state["retrieval_counter"] = state["retrieval_counter"] + 1
            logger.info("node_generate_answer: requesting retrieval")
            logger.info("node_generate_answer: response_json: %s", type(resp))
            logger.info("node_generate_answer: response_json: %s", resp)
            logger.info("node_generate_answer: updated query: %s, ", resp["query"])
            logger.info("node_generate_answer: retrieval_counter: %d", state["retrieval_counter"])
            logger.info("node_generate_answer: updated context: %s", resp["context"])
            return {"action": "retrieve", "query": resp["query"], "context": resp["context"], "retrieval_counter": state["retrieval_counter"]}
        else:
            state["answer"] = resp
            state["action"] = "answer"
            logger.info("node_generate_answer: generated answer: %s", state["answer"])
            return {"action": "response", "answer": state["answer"]}

def node_ask_clarify(state: "OverallState") -> Dict[str, str]:
    """Return a short clarification prompt to the user."""
    msg = state["answer"]
    state["action"] = "clarify"
    logger.info("node_ask_clarify: emitting clarify message")
    return {"action": "clarify", "answer": str(msg)}
    