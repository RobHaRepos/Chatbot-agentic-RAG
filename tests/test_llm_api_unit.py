from types import SimpleNamespace
from typing import Any, cast
from app.llm import llm_api as llm_api_module

def test_health_check_function():
    response = llm_api_module.health_check()
    assert isinstance(response, dict)
    assert response == {"status": "ok"}

def test_retrieve_or_respond_function(monkeypatch):
    # monkeypatch llm_service.retrieve_or_respond to avoid external calls
    def fake_retrieve_or_respond(user_input: str):
        return {"decision": "retrieve", "query": "iphone 16"}

    monkeypatch.setattr(llm_api_module.llm_service, 'retrieve_or_respond', fake_retrieve_or_respond)

    request = llm_api_module.GenQueryRequest(question="What is new?")
    response = llm_api_module.retrieve_or_respond(request)
    assert isinstance(response, dict)
    assert response['decision'] == 'retrieve'

def test_generate_answer_function_with_and_without_context(monkeypatch):
    def fake_generate_answer(user_input: str, retrieved_information: str = ""):
        return f"Q:{user_input}|CTX:{retrieved_information}"

    monkeypatch.setattr(llm_api_module.llm_service, 'generate_answer', fake_generate_answer)

    # with context
    request = llm_api_module.GenQueryRequest(question="What's new?", context="Iphone 16 MAX")
    response = llm_api_module.generate_answer(request)
    assert isinstance(response, dict)
    assert 'answer' in response
    assert 'CTX:Iphone 16 MAX' in response['answer']

    # without context -> context defaults to None so endpoint should pass empty string
    request2 = llm_api_module.GenQueryRequest(question="What's new?")
    response2 = llm_api_module.generate_answer(request2)
    assert isinstance(response2, dict)
    assert 'answer' in response2
    # ensure context placeholder is present and not the string 'None'
    assert 'CTX:' in response2['answer'] and 'CTX:None' not in response2['answer']
