from app.llm.src import llm_api as llm_api_module

DEFAULT_STORE_ID = 1


def test_health_check_function():
    response = llm_api_module.health_check()
    assert isinstance(response, dict)
    assert response == {"status": "ok"}


def test_retrieve_or_respond_function(monkeypatch):
    # monkeypatch llm_service.retrieve_or_respond to avoid external calls
    def fake_retrieve_or_respond(user_input: str, store_id: int):
        return {"action": "retrieve", "query": "iphone 16"}

    monkeypatch.setattr(llm_api_module.llm_service, 'retrieve_or_respond', fake_retrieve_or_respond)

    request = llm_api_module.GenQueryRequest(question="What is new?", store_id=DEFAULT_STORE_ID)
    response = llm_api_module.retrieve_or_respond(request)
    assert isinstance(response, dict)
    assert response['action'] == 'retrieve'


def test_generate_answer_function_with_and_without_context(monkeypatch):
    def fake_generate_answer(user_input: str, retrieved_information: str = "", context: str = "", store_id: int = DEFAULT_STORE_ID):
        return f"Q:{user_input}|Docs:{retrieved_information}|Ctx:{context}"

    monkeypatch.setattr(llm_api_module.llm_service, 'generate_answer', fake_generate_answer)

    # with documents, w/o context
    request = llm_api_module.GenQueryRequest(question="What's new?", documents="Iphone 16 MAX", context="", store_id=DEFAULT_STORE_ID)
    response = llm_api_module.generate_answer(request)
    assert isinstance(response, str)
    assert 'Docs:Iphone 16 MAX' in response

    # w/o documents & w/o context
    request2 = llm_api_module.GenQueryRequest(question="What's new?", documents="", context="", store_id=DEFAULT_STORE_ID)
    response2 = llm_api_module.generate_answer(request2)
    assert isinstance(response2, str)
    assert 'Docs:' in response2 and 'Docs:None' not in response2