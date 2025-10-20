import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import MODEL_NAME_LLM, TEMPERATURE_LLM, MAX_TOKENS
from app.langgraph.tools import get_tools

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
    def __init__(self, Model, model_name: str, api_key: str, max_tokens:int, temperature: float):
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

    def generate(self, prompt: ChatPromptTemplate) -> str:
        return self.llm.invoke(prompt.messages)

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
            
        prompt = ChatPromptTemplate.from_messages(template)
        prompt = prompt.invoke({
                "user_input": user_input,
                "retrieved_information": retrieved_information  
            })
    
        response = self.llm.invoke(prompt.messages)
        return response.content

    def query_or_respond(self, user_input: str, template: list = None) -> str:
        if not template:
            template = ([
            ("system", "You are a helpful AI assistant for a phone shop. Given the user question, "
                 "decide if you can answer it directly or if you need to search for more information. "
                 "If you can answer it directly, return a JSON object: "
                 '{"decision":"answer","answer":"<your answer>"} '
                 "If you need to search for more information in vectorstore, return a JSON object: "
                 '{"decision":"retrieve","query":"<search query>"} '
                 "Return only valid JSON in the response body."),
            ])
            
        prompt = ChatPromptTemplate.from_messages(template)
        prompt = prompt.invoke({
                "user_input": user_input
            })
    
        response = self.llm.invoke(prompt.messages)
        text = getattr(response, "content", str(response)).strip()

        # try parse as JSON first
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "action" in obj:
                return obj
        except Exception:
            pass

        # fallback: simple prefix parsing
        t = text
        if t.upper().startswith("ANSWER:"):
            return {"decision": "answer", "answer": t[len("ANSWER:"):].strip()}
        if t.upper().startswith("SEARCH:"):
            return {"decision": "retrieve", "query": t[len("SEARCH:"):].strip()}

        # fallback default
        return {"decision": "answer", "answer": t}