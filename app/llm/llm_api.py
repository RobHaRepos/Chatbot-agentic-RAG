import os
import ast
from langchain_openai import ChatOpenAI
from fastapi import FastAPI 
from pydantic import BaseModel
from app.llm.llm import AiChatService
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME_LLM = os.environ.get("MODEL_NAME_LLM", "gpt-4.1-mini")
TEMPERATURE_LLM = float(os.environ.get("TEMPERATURE_LLM", 0.0))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 400))
API_KEY_LLM = os.environ.get("OPENAI_API_KEY", None)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        logger.info("LLM API shutting down.")

app = FastAPI(lifespan=lifespan)

llm_service = AiChatService(model_class=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)

class GenRequest(BaseModel):
    prompt: str
    
class GenQueryRequest(BaseModel):
    question: str
    documents: str | None = None
    context: str | None = None

@app.post("/retrieve_or_respond")
def retrieve_or_respond(req: GenQueryRequest):
    response = llm_service.retrieve_or_respond(user_input=req.question)
    return response

@app.post("/generate_answer")
def generate_answer(req: GenQueryRequest):
    logger.info("generate_answer_api: received context: %s", req.context)
    if req.question is None or req.question.strip() == "":
        return {"answer": "I'm sorry, but I need a question to provide an answer."}
    answer = llm_service.generate_answer(
        user_input=req.question, 
        retrieved_information=req.documents if req.documents else "", 
        context=req.context if req.context else ""
        )
    logger.info("generate_answer_api: returned answer: %s", answer)
    if answer.strip().startswith("{"):
        response = ast.literal_eval(answer) 
        return response
    return answer

@app.get("/ready")
def readiness_check():
    ready = getattr(llm_service.llm, "llm", None) is not None
    return {"status": ready}

@app.get("/health")
def health_check():
    return {"status": "ok"}