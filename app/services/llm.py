import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import MODEL_NAME_LLM, TEMPERATURE_LLM, MAX_TOKENS

def define_llm(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, temperature=TEMPERATURE_LLM, max_tokens=MAX_TOKENS):
    llm = Model(
        model=model_name,
        temperature=temperature,
        max_completion_tokens=max_tokens
    )
    return llm


class AiChatService:
    def __init__(self, Model, model_name: str, api_key: str, max_tokens:int, temperature: float):
        self.model_name = model_name
        self.model_class = Model
        self.api_key = os.getenv("OPEN_API_KEY")
        self.max_tokens = max_tokens
        self.temperature = temperature

    def build_prompt(self, question: str, context: str = "", template: str | None = None) -> str:
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
            prompt = ChatPromptTemplate.from_template(template)
        return prompt

    def generate(self, prompt: str) -> str:
        llm = define_llm(self.model_class, self.model_name, self.temperature, self.max_tokens)
        return llm(prompt)