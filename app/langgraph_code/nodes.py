import os
import logging
import httpx
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .workflow import OverallState

LLM_API_URL = os.environ.get("LANGGRAPH_LLM_API_URL", "http://localhost:8002")
RETRIEVER_API_URL = os.environ.get("LANGGRAPH_RETRIEVER_API_URL", "http://localhost:8001")

logger = logging.getLogger("langgraph_nodes")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


async def node_retrieve_string(state: "OverallState") -> Dict[str, Any]:
    payload = {"query": state["question"], "k": state.get("k")}
    logger.info("node_retrieve_string: sending to %s payload=%s", RETRIEVER_API_URL, payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{RETRIEVER_API_URL}/retrieve_documents_string", json=payload)
        try:
            r.raise_for_status()
        except Exception:
            logger.exception("Retriever call failed; status=%s text=%s", getattr(r, 'status_code', None), getattr(r, 'text', None))
            raise
        body = r.json()
        
        logger.info("node_retrieve_string: got body keys=%s; length=%s", (list(body.keys()) if isinstance(body, dict) else type(body)), (len(str(body)) if body else 0))
        logger.info("node_retrieve_string: retrieved documents: %s", str(body))  # log the body
        logger.info("node_retrieve_string: retrieved string: %s", str(body.get("documents", "") )[:500])  # log first 500 chars
        return {"action": "retrieve", "documents": body, "context": body.get("documents", "")}

async def node_retrieve_or_respond(state: "OverallState") -> Dict[str, Any]:
    payload = {"question": state["question"]}
    logger.info("node_retrieve_or_respond: calling LLM %s with payload=%s", LLM_API_URL, payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{LLM_API_URL}/retrieve_or_respond", json=payload)
        r.raise_for_status()
        body = r.json()
        logger.info("node_retrieve_or_respond: LLM returned %s", body)
        if not isinstance(body, dict) or "decision" not in body:
            txt = body if isinstance(body, str) else str(body)
            logger.info("node_retrieve_or_respond: asking to clarify")
            return {"decision": "clarify", "answer": txt}
    return body

async def node_generate_answer(state: "OverallState") -> Dict[str, str]:
    payload = {"question": state["question"], "context": state.get("context", "")}
    logger.info("node_generate_answer: calling LLM %s with payload keys=%s and payload content=%s", LLM_API_URL, list(payload.keys()), payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{LLM_API_URL}/generate_answer", json=payload)
        r.raise_for_status()
        resp = r.json()
        logger.info("node_generate_answer: LLM returned %s", resp)
        return {"action": "answer", "answer": resp.get("answer", "")}

def node_ask_clarify(state: "OverallState") -> Dict[str, str]:
    """Return a short clarification prompt to the user."""
    msg = "The query seems to be unrelated to phones. Could you be more specific? Which phone model or what detail do you mean (brand/model/specs/price)?"
    state["clarification"] = msg
    logger.info("node_ask_clarify: emitting clarify message")
    return {"action": "clarify", "answer": msg}
    