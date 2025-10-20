from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.services.llm import AiChatService
from app.config import MAX_TOKENS, TEMPERATURE_LLM, MODEL_NAME_LLM, API_KEY_LLM

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

def test_generate_response():
    service = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=API_KEY_LLM, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    prompt = ChatPromptTemplate.from_messages([
        ("user", "What is the newest Iphone?")
    ])
    prompt = prompt.invoke({})
    result = service.generate(prompt=prompt)
    print(result.content)
    assert isinstance(result.content, str) 
    assert len(result.content) > 0 
    assert "Iphone 15".lower() in result.content.lower()