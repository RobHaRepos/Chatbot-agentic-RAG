from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.services.llm import AiChatService
from app.config import MAX_TOKENS, TEMPERATURE_LLM, MODEL_NAME_LLM, API_KEY_LLM

def generate_decisions(user_input:str, monkeypatch):    
    def _fake_build_llm(Model, model_name, temperature, max_tokens):
        return Model(
            model=model_name,
            temperature=temperature,
            max_completion_tokens=max_tokens
        )

    monkeypatch.setattr("app.services.llm.build_llm", _fake_build_llm)

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
    

def test_build_prompt_default():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    question = "What is the newest Iphone?"
    context = "The newest Iphone is the Iphone 16 MAX."
    result = service.build_prompt(question=question, context=context)
    messages = result.to_messages()
    human_message = messages[1].content
    system_message = messages[0].content
    print(human_message)
    assert isinstance(human_message, str)
    assert isinstance(system_message, str)
    assert len(messages) > 0
    assert question in human_message
    assert context in system_message

def test_build_prompt_custom():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    question = "What is the newest Iphone?"
    context = "The newest Iphone is the Iphone 16 MAX."
    template = ([
        ("system", "You are a helpful AI assistant for a phone shop. \nContext: {context}"),
        ("user", "Question: {question}")
    ])
    result = service.build_prompt(question=question, context=context, template=template)
    messages = result.to_messages()
    system_message = messages[0].content
    human_message = messages[1].content
    print(system_message)
    assert isinstance(system_message, str)
    assert len(messages) > 0
    assert question in human_message
    assert context in system_message

def test_parameters_llm():
    service = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    assert service.model_name == MODEL_NAME_LLM
    assert service.max_tokens == MAX_TOKENS
    assert service.temperature == TEMPERATURE_LLM

def test_generate_simple_response(monkeypatch):
    
    def _fake_build_llm(Model, model_name, temperature, max_tokens):
        return Model(
            model=model_name,
            temperature=temperature,
            max_completion_tokens=max_tokens
        )
    
    monkeypatch.setattr("app.services.llm.build_llm", _fake_build_llm)
    
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
    
def test_generate_decision_retrieve(monkeypatch):
    decision, content = generate_decisions(user_input="What is the newest Iphone?", monkeypatch=monkeypatch)
    print(f"Decision: {decision}, Content: {content}")
    assert decision == "retrieve"
    assert isinstance(content, str) 
    assert len(content) >= 0
    
def test_generate_decision_clarify(monkeypatch):
    decision, content = generate_decisions(user_input="What is the capital of France?", monkeypatch=monkeypatch)
    print(f"Decision: {decision}, Content: {content}")
    assert decision == "clarify"
    assert isinstance(content, str) 
    assert len(content) >= 0