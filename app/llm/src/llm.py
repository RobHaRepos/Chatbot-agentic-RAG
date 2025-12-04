import ast
import logging
import os
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.llm.src.template_manager import TemplateManager
from app.logger_service.handlers import HTTPLogHandler

MODEL_NAME_LLM = os.environ.get("MODEL_NAME_LLM", "gpt-4.1-mini")
TEMPERATURE_LLM = float(os.environ.get("TEMPERATURE_LLM", 0.0))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 400))
LOGGER_SERVICE_URL = os.environ.get("LOGGER_SERVICE_URL", "http://localhost:8004")
RETRIEVER_SERVICE_URL = os.environ.get("RETRIEVER_SERVICE_URL", "http://localhost:8001")

logger = logging.getLogger("llm_service")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
remote = HTTPLogHandler(LOGGER_SERVICE_URL)
logger.addHandler(remote)
logger.setLevel(logging.INFO)

class AiChatService:
    """Service for LLM-based chat operations with dynamic template loading."""
    def __init__(
        self, 
        model_class, 
        model_name: str, 
        api_key: str | None, 
        max_tokens: int, 
        temperature: float, 
        template_manager: TemplateManager
    ):
        """Initialize the AiChatService with LLM parameters and template manager."""
        self.model_name = model_name
        self.model_class = model_class
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.llm = self.build_llm(self.model_class, self.model_name, self.temperature, self.max_tokens)
        self.template_manager = template_manager
        self._current_store_id: int | None = None

    def _ensure_store_id(self, store_id: int | None, method_name: str) -> int:
        """Validate and return store_id, raising if not available."""
        resolved_id = store_id or self._current_store_id
        if resolved_id is None:
            logger.error("%s: store_id must be set either via parameter or set_store()", method_name)
            raise ValueError("store_id must be set either via parameter or set_store()")
        
        if self._current_store_id != resolved_id:
            logger.info("Switching to store_id=%s", resolved_id)
            self._current_store_id = resolved_id
        
        return resolved_id
    
    def extract_llm_response_content(self, template: Any, variables: Dict[str, Any], llm: Any) -> str:
        """Extract content from LLM response using the provided template and variables."""
        prompt = ChatPromptTemplate.from_messages(template)
        prompt = prompt.invoke(variables)

        messages = getattr(prompt, "messages", None)
        if messages is None:
            logger.error("extract_llm_response_content: unsupported prompt type is %s", type(prompt))
            raise TypeError("Unsupported prompt type: expected a rendered PromptValue or ChatPromptTemplate")

        response = llm.invoke(messages)
        logger.debug("LLM full response: %s", response)
        content = getattr(response, "content", "").strip()
        logger.info("extract_llm_response_content: extracted content: %s", content)
        return content

    def build_llm(self, model_class=ChatOpenAI, model_name=MODEL_NAME_LLM, temperature=TEMPERATURE_LLM, max_tokens=MAX_TOKENS):
        """Build and return an LLM instance with the specified parameters."""
        llm = model_class(
            model=model_name,
            temperature=temperature,
            max_completion_tokens=max_tokens
        )
        logger.info("build_llm: created LLM instance=%s", llm)
        return llm

    def generate(self, prompt: Any) -> Any:
        """Invoke LLM directly with a pre-built prompt."""
        logger.info("generate: invoking LLM with prompt=%s", prompt)
        return self.llm.invoke(prompt.messages)

    def generate_answer(
        self, 
        user_input: str, 
        retrieved_information: str = "", 
        context: str = "", 
        store_id: int | None = None
    ) -> str:
        """Generate an answer based on user input, retrieved information, and context."""
        store_id = self._ensure_store_id(store_id, "generate_answer")
        template = self.template_manager.get_template(store_id, "generate_answer")
        
        content = self.extract_llm_response_content(
            template,
            {
                "user_input": user_input,
                "retrieved_information": retrieved_information,
                "context": context
            },
            self.llm
        )
        logger.info("generate_answer: generated answer: %s", content)
        return str(content)

    def retrieve_or_respond(self, user_input: str, store_id: int | None = None) -> Dict[str, Any]:
        """Decide whether to retrieve more information or clarify the user question."""
        store_id = self._ensure_store_id(store_id, "retrieve_or_respond")
        template = self.template_manager.get_template(store_id, "retrieve_or_respond")
        
        content = self.extract_llm_response_content(template, {"user_input": user_input}, self.llm)
        
        if "action" in content:
            parsed = ast.literal_eval(content)
            logger.info("retrieve_or_respond: parsed LLM response: %s", parsed)
            return parsed
        
        logger.warning("retrieve_or_respond: falling back to clarify")
        return {"action": "clarify", "answer": " "}