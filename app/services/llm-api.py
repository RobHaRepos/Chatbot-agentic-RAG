import os
from langchain_openai import ChatOpenAI
from fastapi import FastAPI 
from pydantic import BaseModel
from app.services.llm import AiChatService
from app.config import MODEL_NAME_LLM, TEMPERATURE_LLM, MAX_TOKENS, API_KEY_LLM

app = FastAPI()

llm_service = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)

class GenRequest(BaseModel):
    prompt: str
    
class GenQueryRequest(BaseModel):
    question: str
    context: str | None = None

@app.post("/generate")
def generate(req: GenRequest):
    prompt = llm_service.build_prompt(question=req.prompt)
    return {"text": llm_service.generate(prompt)}

@app.post("/generate_search_query")
def generate_search_query(req: GenQueryRequest):
    query = llm_service.generate_search_query(user_input=req.question, retrieved_information=req.context if req.context else "")
    return {"query": query}

@app.post("/retrieve_or_respond")
def retrieve_or_respond(req: GenQueryRequest):
    response = llm_service.retrieve_or_respond(user_input=req.question)
    return response

@app.post("/generate_answer")
def generate_answer(req: GenQueryRequest):
    answer = llm_service.generate_answer(question=req.question, retrieved_information=req.context if req.context else "")
    return {"answer": answer}

@app.get("/ready")
def readiness_check():
    ready = llm_service.llm is not None
    return {"status": ready}

@app.post("/health")
def health_check():
    return {"status": "ok"}