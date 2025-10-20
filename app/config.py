from pathlib import Path
import os

PATH_TO_FAISS_INDEX = str(Path(__file__).resolve().parent.parent / "faiss_Hugging_index")
MODEL_NAME_EMBEDDING = "sentence-transformers/all-MiniLM-L6-v2"

NUMBER_OF_DOCUMENTS_TO_RETRIEVE = 5

MODEL_NAME_LLM = "gpt-4.1-mini"
TEMPERATURE_LLM = 0.0
MAX_TOKENS = 400

API_KEY_LLM = os.getenv("OPENAI_API_KEY")