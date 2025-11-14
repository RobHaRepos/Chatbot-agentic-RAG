import pytest
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.llm.llm import AiChatService
from app.config import MAX_TOKENS, TEMPERATURE_LLM, MODEL_NAME_LLM, API_KEY_LLM
from types import SimpleNamespace


BASE_URL = "http://localhost:8002"
# ToDO -- write integration tests with real LLM calls -- requires OPENAI_API_KEY in env

@pytest.fixture()
def patch_build_llm(monkeypatch):
    """Default fake LLM for unit tests: returns harmless answer string."""
    fake_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="The newest Iphone is Iphone 15 Pro Max."))
    monkeypatch.setattr(AiChatService, "build_llm", lambda self, *a, **k: fake_llm)
    return fake_llm

def generate_actions(user_input:str):    
    service = AiChatService(
        model_class=ChatOpenAI, 
        model_name=MODEL_NAME_LLM, 
        api_key=API_KEY_LLM, 
        max_tokens=MAX_TOKENS, 
        temperature=TEMPERATURE_LLM
        )

    result = service.retrieve_or_respond(user_input=user_input)
    content = result.get("answer", "")
    action = result.get("action", "")

    return action, content

def test_parameters_llm():
    service = AiChatService(model_class=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    assert service.model_name == MODEL_NAME_LLM
    assert service.max_tokens == MAX_TOKENS
    assert service.temperature == TEMPERATURE_LLM

@pytest.mark.usefixtures("patch_build_llm")
def test_generate_simple_response():    
    service = AiChatService(
        model_class=ChatOpenAI, 
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

@pytest.mark.usefixtures("patch_build_llm")
def test_extract_llm_response_content_happy():    
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

@pytest.mark.usefixtures("patch_build_llm")
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

@pytest.mark.usefixtures("patch_build_llm")
def test_generate_action_retrieve(monkeypatch):
    monkeypatch.setattr(AiChatService, "retrieve_or_respond", lambda self, user_input: {"action": "retrieve", "answer": ""})
    action, content = generate_actions(user_input="What is the newest Iphone?", )
    print(f"Action: {action}, Content: {content}")
    assert action == "retrieve"
    assert isinstance(content, str) 
    
@pytest.mark.usefixtures("patch_build_llm")
def test_generate_action_clarify(monkeypatch):
    monkeypatch.setattr(AiChatService, "retrieve_or_respond", lambda self, user_input: {"action": "clarify", "answer": ""})
    action, content = generate_actions(user_input="What is the capital of France?", )
    print(f"Action: {action}, Content: {content}")
    assert action == "clarify"
    assert isinstance(content, str) 

@pytest.mark.usefixtures("patch_build_llm")
def test_retrieve_or_respond_fallback(monkeypatch):
    monkeypatch.setattr(AiChatService, "build_llm",
                        lambda self, *a, **k: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="Non-JSON response")))

    monkeypatch.setattr(AiChatService, "extract_llm_response_content",
                        lambda self, template, variables, llm: "Non-JSON response")

    svc = AiChatService(model_class=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM,
                        max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)

    result = svc.retrieve_or_respond(user_input="Some unrelated question")
    assert result.get("action") == "clarify"
    assert isinstance(result.get("answer", ""), str)


class TestGenerateAnswer:
    def setup_method(self) -> None:
        self.service = AiChatService(
            model_class=ChatOpenAI, 
            model_name=MODEL_NAME_LLM, 
            api_key=API_KEY_LLM, 
            max_tokens=MAX_TOKENS, 
            temperature=TEMPERATURE_LLM
            )

    def test_generate_answer(self):
        """Test generate_answer with normal input."""
        answer = self.service.generate_answer(
            user_input="What is the newest Iphone?", 
            retrieved_information="Iphone 16 MAX, \
                Release: September 2024.",
            context="It has a big display."
            )
        print(f"Answer: {answer}")
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert "Iphone 16".lower() in answer.lower()
        
    def test_generate_retrieve(self):
        """Test generate_answer leading to retrieve action."""

        answer = self.service.generate_answer(
            user_input="What is the newest Iphone?", 
            retrieved_information="The phone has a big battery",
            context="It has a big display"
            ) 
        print(f"Answer leading to retrieve: {answer}")

        assert "action" in answer
        assert "retrieve" in answer
        assert "query" in answer
        assert "context" in answer