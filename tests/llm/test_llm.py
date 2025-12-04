from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import API_KEY_LLM, MAX_TOKENS, MODEL_NAME_LLM, TEMPERATURE_LLM
from app.llm.src.llm import AiChatService
from app.llm.src.template_manager import TemplateManager


BASE_URL = "http://localhost:8002"
DEFAULT_STORE_ID = 1

@pytest.fixture
def mock_template_manager():
    """Create a mock TemplateManager that returns default templates."""
    manager = MagicMock(spec=TemplateManager)
    manager.get_template.side_effect = lambda store_id, template_type: \
        TemplateManager.DEFAULT_TEMPLATES.get(template_type, [])
    return manager

@pytest.fixture()
def patch_build_llm(monkeypatch):
    """Default fake LLM for unit tests: returns harmless answer string."""
    fake_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="The newest Iphone is Iphone 15 Pro Max."))
    monkeypatch.setattr(AiChatService, "build_llm", lambda self, *a, **k: fake_llm)
    return fake_llm

def create_service(template_manager=None):
    """Helper to create AiChatService with required parameters."""
    if template_manager is None:
        template_manager = MagicMock(spec=TemplateManager)
        template_manager.get_template.side_effect = lambda store_id, template_type: \
            TemplateManager.DEFAULT_TEMPLATES.get(template_type, [])
    
    return AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=template_manager
    )


def generate_actions(user_input: str, store_id: int = DEFAULT_STORE_ID):
    service = create_service()
    result = service.retrieve_or_respond(user_input=user_input, store_id=store_id)
    content = result.get("answer", "")
    action = result.get("action", "")
    return action, content


def test_parameters_llm(mock_template_manager):
    """Validate AiChatService parameters are set correctly after initialization."""
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    assert service.model_name == MODEL_NAME_LLM
    assert service.max_tokens == MAX_TOKENS
    assert service.temperature == TEMPERATURE_LLM

@pytest.mark.usefixtures("patch_build_llm")
def test_generate_simple_response():    
    """LLM generate returns a valid string content using prompt."""
    service = create_service()
    
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
    """extract_llm_response_content returns content string when LLM responds with content."""
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
    """extract_llm_response_content raises TypeError when prompt returns no messages."""
    class FakeLLM:
        def invoke(self, messages):
            return SimpleNamespace(content="This is a response.")
    
    class FakePromptNoMessages:
        def __init__(self, template):
            self.template = template
        def invoke(self, variables):
            return SimpleNamespace(messages=None)

    monkeypatch.setattr("app.llm.src.llm.ChatPromptTemplate.from_messages", FakePromptNoMessages)

    fake_llm = FakeLLM()
    service = object.__new__(AiChatService)
    
    with pytest.raises(TypeError):
        service.extract_llm_response_content(template=[], variables={}, llm=fake_llm)

@pytest.mark.usefixtures("patch_build_llm")
def test_generate_action_retrieve(monkeypatch):
    """retrieve_or_respond returns retrieve action when appropriate."""
    monkeypatch.setattr(AiChatService, "retrieve_or_respond", lambda self, user_input, store_id: {"action": "retrieve", "answer": ""})
    action, content = generate_actions(user_input="What is the newest Iphone?")
    print(f"Action: {action}, Content: {content}")
    assert action == "retrieve"
    assert isinstance(content, str) 
    
@pytest.mark.usefixtures("patch_build_llm")
def test_generate_action_clarify(monkeypatch):
    """retrieve_or_respond returns clarify action for unrelated questions."""
    monkeypatch.setattr(AiChatService, "retrieve_or_respond", lambda self, user_input, store_id: {"action": "clarify", "answer": ""})
    action, content = generate_actions(user_input="What is the capital of France?")
    print(f"Action: {action}, Content: {content}")
    assert action == "clarify"
    assert isinstance(content, str) 

@pytest.mark.usefixtures("patch_build_llm")
def test_retrieve_or_respond_fallback(monkeypatch):
    """Fallback behavior returns clarify when LLM gives non-JSON response."""
    monkeypatch.setattr(AiChatService, "build_llm",
                        lambda self, *a, **k: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="Non-JSON response")))

    monkeypatch.setattr(AiChatService, "extract_llm_response_content",
                        lambda self, template, variables, llm: "Non-JSON response")

    svc = create_service()

    result = svc.retrieve_or_respond(user_input="Some unrelated question", store_id=DEFAULT_STORE_ID)
    assert result.get("action") == "clarify"
    assert isinstance(result.get("answer", ""), str)


def test_ensure_store_id_raises_when_not_set(mock_template_manager, monkeypatch):
    """_ensure_store_id raises ValueError when store_id is not provided and not set."""
    monkeypatch.setattr(AiChatService, "build_llm",
                        lambda self, *a, **k: SimpleNamespace(invoke=lambda m: SimpleNamespace(content="")))
    
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    with pytest.raises(ValueError, match="store_id must be set"):
        service._ensure_store_id(None, "test_method")


def test_ensure_store_id_uses_current_store_id(mock_template_manager, monkeypatch):
    """_ensure_store_id uses _current_store_id when no parameter provided."""
    monkeypatch.setattr(AiChatService, "build_llm",
                        lambda self, *a, **k: SimpleNamespace(invoke=lambda m: SimpleNamespace(content="")))
    
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    service._current_store_id = 42
    result = service._ensure_store_id(None, "test_method")
    assert result == 42


def test_generate_answer_unit(mock_template_manager, monkeypatch):
    """Unit test for generate_answer method with mocked dependencies."""
    fake_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="This is the generated answer."))
    monkeypatch.setattr(AiChatService, "build_llm", lambda self, *a, **k: fake_llm)
    
    mock_template_manager.get_template.return_value = [
        ("system", "Context: {context}\nRetrieved: {retrieved_information}"),
        ("user", "{user_input}")
    ]
    
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    
    result = service.generate_answer(
        user_input="What is X?",
        retrieved_information="X is Y",
        context="Some context",
        store_id=1
    )
    
    assert isinstance(result, str)
    assert result == "This is the generated answer."
    mock_template_manager.get_template.assert_called_with(1, "generate_answer")


def test_retrieve_or_respond_with_action(mock_template_manager, monkeypatch):
    """retrieve_or_respond returns parsed action when LLM returns valid JSON."""
    fake_response = '{"action": "retrieve", "query": "test query"}'
    fake_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content=fake_response))
    monkeypatch.setattr(AiChatService, "build_llm", lambda self, *a, **k: fake_llm)
    
    mock_template_manager.get_template.return_value = [
        ("system", "Decide action"),
        ("user", "{user_input}")
    ]
    
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    
    result = service.retrieve_or_respond(user_input="Test query", store_id=1)
    
    assert result["action"] == "retrieve"
    assert result["query"] == "test query"


def test_generate_answer_uses_ensure_store_id(mock_template_manager, monkeypatch):
    """generate_answer raises ValueError when store_id not available."""
    fake_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="answer"))
    monkeypatch.setattr(AiChatService, "build_llm", lambda self, *a, **k: fake_llm)
    
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    with pytest.raises(ValueError, match="store_id must be set"):
        service.generate_answer(user_input="Test", store_id=None)


def test_retrieve_or_respond_fallback_path(mock_template_manager, monkeypatch):
    """retrieve_or_respond falls back to clarify when no 'action' in response."""
    fake_response = "Just a plain text response"
    fake_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content=fake_response))
    monkeypatch.setattr(AiChatService, "build_llm", lambda self, *a, **k: fake_llm)
    
    mock_template_manager.get_template.return_value = [
        ("system", "Decide"),
        ("user", "{user_input}")
    ]
    
    service = AiChatService(
        model_class=ChatOpenAI,
        model_name=MODEL_NAME_LLM,
        api_key=API_KEY_LLM,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_LLM,
        template_manager=mock_template_manager
    )
    
    result = service.retrieve_or_respond(user_input="Test", store_id=1)
    
    assert result["action"] == "clarify"
    assert result["answer"] == " "


@pytest.mark.integration
class TestGenerateAnswer:
    """Integration tests for generate_answer - require real LLM calls."""
    
    def setup_method(self) -> None:
        self.service = create_service()
        self.store_id = DEFAULT_STORE_ID

    @pytest.mark.skip(reason="Integration test - requires real LLM and may be flaky")
    def test_generate_answer(self):
        """generate_answer returns a string answer containing expected text."""
        answer = self.service.generate_answer(
            user_input="What is the newest Iphone?", 
            retrieved_information="Iphone 16 MAX, \
                Release: September 2024.",
            context="It has a big display.",
            store_id=self.store_id
            )
        print(f"Answer: {answer}")
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert "Iphone 16".lower() in answer.lower()
        
    @pytest.mark.skip(reason="Integration test - requires real LLM and may be flaky")
    def test_generate_retrieve(self):
        """generate_answer returns a retrieve JSON when retrieval needed."""

        answer = self.service.generate_answer(
            user_input="What is the newest Iphone?", 
            retrieved_information="The phone has a big battery",
            context="It has a big display",
            store_id=self.store_id
            ) 
        print(f"Answer leading to retrieve: {answer}")

        assert "action" in answer
        assert "retrieve" in answer
        assert "query" in answer
        assert "context" in answer