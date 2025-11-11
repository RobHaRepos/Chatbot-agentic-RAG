import os
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, Optional, Dict

MODEL_NAME_LLM = os.environ.get("MODEL_NAME_LLM", "gpt-4.1-mini")
TEMPERATURE_LLM = float(os.environ.get("TEMPERATURE_LLM", 0.0))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 400))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AiChatService:
    def __init__(self, model_class, model_name: str, api_key: str | None, max_tokens:int, temperature: float):
        self.model_name = model_name
        self.model_class = model_class
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.llm = self.build_llm(self.model_class, self.model_name, self.temperature, self.max_tokens)

    def extract_llm_response_content(self, template: Any, variables: Dict[str, Any], llm: Any) -> str:
        prompt = ChatPromptTemplate.from_messages(template)
        prompt = prompt.invoke(variables)

        messages = getattr(prompt, "messages", None)
        if messages is None:
            logger.error("extract_llm_response_content: unsupported prompt type is %s", type(prompt))
            raise TypeError("Unsupported prompt type: expected a rendered PromptValue or ChatPromptTemplate")

        response = llm.invoke(messages)
        content = getattr(response, "content", "").strip()
        logger.info("extract_llm_response_content: extracted content=%s", content)
        return str(content)

    def build_llm(self, model_class=ChatOpenAI, model_name=MODEL_NAME_LLM, temperature=TEMPERATURE_LLM, max_tokens=MAX_TOKENS):
        llm = model_class(
            model=model_name,
            temperature=temperature,
            max_completion_tokens=max_tokens
        )
        logger.info("build_llm: created LLM instance=%s", llm)
        return llm

    def generate(self, prompt: Any) -> Any:
        logger.info("generate: invoking LLM with prompt=%s", prompt)
        return self.llm.invoke(prompt.messages)
    
    def generate_answer(self, user_input: str, retrieved_information: str = "", template: list = []) -> str:
        if not template:
            template = ([
                ("system", "You are a helpful AI assistant for a phone shop. \
                Given the user question and the information from the documents, \
                generate a concise and accurate answer. \n \
                USER QUESTION: {user_input} \n \
                INFORMATION FROM DOCUMENTS: {retrieved_information} \n\n \
                Don't make up an answer."), 
            ])
            logger.info("generate_answer: no template provided, using default.")
        content = self.extract_llm_response_content(template, {"user_input": user_input, "retrieved_information": retrieved_information}, self.llm)
        logger.info("generate_answer: generated answer=%s", content)
        return str(content)

    def retrieve_or_respond(self, user_input: str, template: Optional[list[tuple[str, str]]] = None) -> Dict[str, Any]:
        if not template:
            template = ([
            ("system", "You are a helpful AI assistant for a phone shop. Given the user question, "
                 "decide if you need clarification from the user or if you need to search for more information. "
                 "If the user question is unrelated to phones: "
                 '{{"decision":"clarify","answer":" "}} '
                 "If the user question is related to phones: "
                 '{{"decision":"retrieve","query":" "}} '
                 "Return only valid JSON in the response body."),
            ("user", "User question: {user_input}")
            ])
            logger.info("retrieve_or_respond: no template provided, using default.")
        content = self.extract_llm_response_content(template, {"user_input": user_input}, self.llm)
        
        try:
            obj = json.loads(content)
            if isinstance(obj, dict) and ("decision" in obj or "action" in obj):
                logger.info("retrieve_or_respond: parsed LLM response=%s", obj)
                return obj
        except Exception:
            logger.exception("retrieve_or_respond: failed to parse LLM response content=%s", content)

        # fallback
        logger.warning("retrieve_or_respond: falling back to clarify")
        return {"decision": "clarify", "answer": " "}