import os
import ast
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, Dict
from app.logger_service.handlers import HTTPLogHandler

MODEL_NAME_LLM = os.environ.get("MODEL_NAME_LLM", "gpt-4.1-mini")
TEMPERATURE_LLM = float(os.environ.get("TEMPERATURE_LLM", 0.0))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 400))
LOGGER_SERVICE_URL = os.environ.get("LOGGER_SERVICE_URL", "http://localhost:8004")

logger = logging.getLogger("llm_service")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
remote = HTTPLogHandler(LOGGER_SERVICE_URL)
logger.addHandler(remote)
logger.setLevel(logging.INFO)

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
        print("LLM full response: ", response)
        content = getattr(response, "content", "").strip()
        logger.info("extract_llm_response_content: extracted content:%s", content)
        return content

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

    def generate_answer(self, user_input: str, retrieved_information: str = "", context: str = "") -> str:
        template = ([
            ("system", "You are a helpful AI assistant for a phone shop. "
            "Given the user question, retrieved document information, and past context, do the following steps:\n"
            "Step 1: Evaluate, if you can answer all parts of the user question.\n"
            "Step 2: Consider the rules:\n"
            "1. If multiple models  in the documents, prefer the one named in context as 'Newest'.\n"
            "2. Use documents only when they unambiguously match the model.\n"
            "3. Mind about SINGULAR/plural forms in user question and documents.\n" 
            "Step 3: If you CANNOT answer all parts of the user question,:\n"
            "First: seperate eacht part of the user question that you cannot answer with the given information.\n"
            "Second: Write a RAG query that focuses on just ONE of the missing information pieces.\n"
            "Third: RETURN ONLY a single JSON object that strictly conforms to this exact schema:\n"
            '{{"action":"retrieve","query":"<short RAG query — focused always just on one of the missing information pieces>", "context": "<concatenated and summarized infos of all for the user question relevant infos>"}}\n\n'
            "Step 4: If you have ALL information to answer ALL parts of the user question, "
            "return a concise, accurate answer as plain text.\n"
            "USER QUESTION: {user_input}\n"
            "INFORMATION FROM DOCUMENTS: {retrieved_information}\n"
            "CONTEXT: {context}\n"
            "Don't make up an answer.\n"
            "Example:\n"
            "User question: What is the newest Iphone and what display does it have?\n"
            "retrieved Docs: Iphone 13 and released 2022\n"
            '{{"action":"retrieve","query":"Display of the Iphone 13", "context": "Newest Iphone is Iphone 13, Released 2022"}}\n\n'),
        ])
        content = self.extract_llm_response_content(
            template,
            {"user_input": user_input,
             "retrieved_information": retrieved_information,
             "context": context},
            self.llm)
        logger.info("generate_answer: generated answer: %s", content)
        return str(content)

    def retrieve_or_respond(self, user_input: str) -> Dict[str, Any]:
        template = ([
        ("system", "You are a helpful AI assistant for a phone shop. Given the user question, "
                "decide if you need clarification from the user or if you need to search for more information. "
                "If the user question is unrelated to phones: "
                '{{"action":"clarify","answer":" "}} '
                "If the user question is related to phones: "
                '{{"action":"retrieve"}} '
                "Return only valid JSON in the response body."),
        ("user", "User question: {user_input}")
        ])
        content = self.extract_llm_response_content(template, {"user_input": user_input}, self.llm)
        
        if("action" in content):
            content = ast.literal_eval(content)
            logger.info("retrieve_or_respond: parsed LLM response: %s", content)
            return content
        else:
            logger.warning("retrieve_or_respond: falling back to clarify")
            return {"action": "clarify", "answer": " "}