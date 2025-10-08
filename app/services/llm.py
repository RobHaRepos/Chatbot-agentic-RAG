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
        self.llm = define_llm(self.model_class, self.model_name, self.temperature, self.max_tokens)

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
            prompt = ChatPromptTemplate.from_messages(template)
            prompt = prompt.invoke({
                    "question": question,
                    "context": context  
                })
        return prompt

    def generate(self, prompt) -> str:
        return self.llm.invoke(prompt.messages)
    
    def generate_search_query(self, user_input: str, retrieved_information: str = "", template: str | None = None) -> str:
        if not template:
            template = ([
                ("system", "You are a helpful AI assistant for a phone shop. \
                Given the user question and the information from the documents, \
                generate a search query that would help you find more relevant information. \n \
                USER QUESTION: {user_input} \n \
                INFORMATION FROM DOCUMENTS: {retrieved_information} \n\n \
                Produce a short (3-8 words) search query"), 
            ])
            
        prompt = ChatPromptTemplate.from_messages(template)
        prompt = prompt.invoke({
                "user_input": user_input,
                "retrieved_information": retrieved_information  
            })
    
        response = self.llm.invoke(prompt.messages)
        return response.content