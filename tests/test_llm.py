import pytest
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.llm.llm import AiChatService
from app.config import MAX_TOKENS, TEMPERATURE_LLM, MODEL_NAME_LLM, API_KEY_LLM
from types import SimpleNamespace

BASE_URL = "http://localhost:8002"

def generate_decisions(user_input:str):    
    service = AiChatService(
        Model=ChatOpenAI, 
        model_name=MODEL_NAME_LLM, 
        api_key=API_KEY_LLM, 
        max_tokens=MAX_TOKENS, 
        temperature=TEMPERATURE_LLM
        )

    result = service.retrieve_or_respond(user_input=user_input)
    content = result.get("answer", "")
    decision = result.get("decision", "")

    return decision, content

def test_parameters_llm():
    service = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    assert service.model_name == MODEL_NAME_LLM
    assert service.max_tokens == MAX_TOKENS
    assert service.temperature == TEMPERATURE_LLM

def test_generate_simple_response(monkeypatch):    
    service = AiChatService(
        Model=ChatOpenAI, 
        model_name=MODEL_NAME_LLM, 
        api_key=API_KEY_LLM, 
        max_tokens=MAX_TOKENS, 
        temperature=TEMPERATURE_LLM
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("user", "What is the newest Iphone?")
    ])
    prompt = prompt.invoke({})
    result = service.generate(prompt=prompt)
    print(result.content)
    assert isinstance(result.content, str) 
    assert len(result.content) > 0 
    assert "Iphone 15".lower() in result.content.lower()

def test_extract_llm_response_content_happy(monkeypatch):    
    class FakeLLM:
        def invoke(self, messages):
            return SimpleNamespace(content="The newest Iphone is Iphone 15.")
    
    fake_llm = FakeLLM()
    service = object.__new__(AiChatService)
    
    template = [
        ("system", "USER QUESTION: {user_input}"),
    ]
    response = service.extract_llm_response_content(template, {"user_input": "What is the newest Iphone?"}, fake_llm)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Iphone 15".lower() in response.lower()

def test_extract_llm_response_content_sad(monkeypatch):
    class FakeLLM:
        def invoke(self, messages):
            return SimpleNamespace(content="This is a response.")
    
    class FakePromptNoMessages:
        def __init__(self, template):
            self.template = template
        def invoke(self, variables):
            return SimpleNamespace(messages=None)

    monkeypatch.setattr("app.llm.llm.ChatPromptTemplate.from_messages", FakePromptNoMessages)

    fake_llm = FakeLLM()
    service = object.__new__(AiChatService)
    
    with pytest.raises(TypeError):
        service.extract_llm_response_content(template=[], variables={}, llm=fake_llm)

def test_generate_decision_retrieve():
    decision, content = generate_decisions(user_input="What is the newest Iphone?", )
    print(f"Decision: {decision}, Content: {content}")
    assert decision == "retrieve"
    assert isinstance(content, str) 
    #assert len(content) == 0
    
def test_generate_decision_clarify():
    decision, content = generate_decisions(user_input="What is the capital of France?", )
    print(f"Decision: {decision}, Content: {content}")
    assert decision == "clarify"
    assert isinstance(content, str) 
    #assert len(content) > 0

def test_retrieve_or_respond_fallback(monkeypatch):
    monkeypatch.setattr(AiChatService, "build_llm",
                        lambda self, *a, **k: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="Non-JSON response")))

    # Optionally stub extract_llm_response_content to focus on parse fallback:
    monkeypatch.setattr(AiChatService, "extract_llm_response_content",
                        lambda self, template, variables, llm: "Non-JSON response")

    svc = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM,
                        max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)

    result = svc.retrieve_or_respond(user_input="Some unrelated question")
    assert result.get("decision") == "clarify"
    assert isinstance(result.get("answer", ""), str)

def test_generate_full_answer(monkeypatch):
    service = AiChatService(
        Model=ChatOpenAI, 
        model_name=MODEL_NAME_LLM, 
        api_key=API_KEY_LLM, 
        max_tokens=MAX_TOKENS, 
        temperature=TEMPERATURE_LLM
        )

    answer = service.generate_answer(
        user_input="What is the newest Iphone?", 
        retrieved_information="Iphone 16 MAX, \
            Release: September 2024, \
            Feature: 6.7-inch display, \
            improved camera system."
        )
    print(f"Answer: {answer}")
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "Iphone 16 MAX".lower() in answer.lower()