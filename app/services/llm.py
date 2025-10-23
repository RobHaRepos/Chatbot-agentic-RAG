import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import MODEL_NAME_LLM, TEMPERATURE_LLM, MAX_TOKENS
from app.langgraph.tools import get_tools
from typing import Any, Optional, Dict

def extract_llm_response_content(template: Any, variables: Dict[str, Any], llm: Any) -> str:
    prompt = ChatPromptTemplate.from_messages(template)
    prompt = prompt.invoke(variables)

    messages = getattr(prompt, "to_messages", None)
    if callable(messages):
        messages = prompt.to_messages()
    else:
        messages = getattr(prompt, "messages", None)
    
    if messages is None:
        raise TypeError("Unsupported prompt type: expected a rendered PromptValue or ChatPromptTemplate")

    response = llm.invoke(messages)
    content = getattr(response, "content", "").strip()
    return str(content)

def build_llm(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, temperature=TEMPERATURE_LLM, max_tokens=MAX_TOKENS):
    llm = Model(
        model=model_name,
        temperature=temperature,
        max_completion_tokens=max_tokens
    )
    tools = get_tools() 
    llm_with_tools = llm.bind_tools(tools)
    #llm_with_tools = llm
    return llm_with_tools
class AiChatService:
    def __init__(self, Model, model_name: str, api_key: str | None, max_tokens:int, temperature: float):
        self.model_name = model_name
        self.model_class = Model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.llm = build_llm(self.model_class, self.model_name, self.temperature, self.max_tokens)

    def build_prompt(self, question: str, context: str = "", template = None):
        if template is None:
            template = ([
            ("system", "You are a helpful AI assistant for a phone shop. Use the following pieces of context to answer the user question. \
            If you dont know the anwer, just say that you don`t know and don`t try to make up an answer. \n \
            CONTEXT: {context}"),
            ("user", "{question}")
            ])
            
            prompt = ChatPromptTemplate.from_messages(template)
            prompt = prompt.invoke({
                    "question": question,
                    "context": context  
                })
        else:
            prompt = ChatPromptTemplate.from_messages(template)
            prompt = prompt.invoke({
                    "question": question,
                    "context": context  
                })

        print(prompt)
        return prompt

    def generate(self, prompt: Any) -> Any:
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
        content = extract_llm_response_content(template, {"user_input": user_input, "retrieved_information": retrieved_information}, self.llm)
        return str(content)

    def generate_search_query(self, user_input: str, retrieved_information: str = "", template: list = []) -> str:
        if not template:
            template = ([
                ("system", "You are a helpful AI assistant for a phone shop. \
                Given the user question and the information from the documents, \
                generate a search query that would help you find more relevant information. \n \
                USER QUESTION: {user_input} \n \
                INFORMATION FROM DOCUMENTS: {retrieved_information} \n\n \
                Produce a short (3-8 words) search query"), 
            ])
        content = extract_llm_response_content(template, {"user_input": user_input, "retrieved_information": retrieved_information}, self.llm)
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
        content = extract_llm_response_content(template, {"user_input": user_input}, self.llm)

        # try parse as JSON first
        try:
            obj = json.loads(content)
            if isinstance(obj, dict) and ("decision" in obj or "action" in obj):
                return obj
        except Exception:
            pass

        # fallback default
        return {"decision": "clarify", "answer": " "}