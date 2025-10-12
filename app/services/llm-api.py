from fastapi import FastAPI 
from pydantic import BaseModel
from app.services.llm import AiChatService
from app.config import MODEL_NAME_LLM, TEMPERATURE_LLM, MAX_TOKENS

app = FastAPI()
# reuse the factory in app.services.llm instead of re-declaring the model details here
llm_service = AiChatService(Model=None, model_name=MODEL_NAME_LLM, api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)

class GenRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate(req: GenRequest):
    return {"text": llm_service.generate(req.prompt)}