from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.services.llm import AiChatService
from app.config import MAX_TOKENS, TEMPERATURE_LLM, MODEL_NAME_LLM

def test_build_prompt_default():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    question = "What is the newest Iphone?"
    context = "The newest Iphone is the Iphone 16 MAX."
    result = service.build_prompt(question=question, context=context)
    system_message = result.messages[0].content
    human_message = result.messages[1].content
    print(system_message)
    assert isinstance(system_message, str) and len(result.messages) > 0 and question in human_message and context in system_message

def test_build_prompt_custom():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    question = "What is the newest Iphone?"
    context = "The newest Iphone is the Iphone 16 MAX."
    template = ([
        ("system", "Your are a helpful AI assistant for a phone shop. \nA: {context}"),
        ("user", "Q: {question}")
    ])
    result = service.build_prompt(question=question, context=context, template=template)
    system_message = result.messages[0].content
    human_message = result.messages[1].content
    print(system_message)
    assert isinstance(system_message, str) and len(result.messages) > 0 and question in human_message and context in system_message

def test_parameters_llm():
    service = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    assert service.model_name == MODEL_NAME_LLM
    assert service.max_tokens == MAX_TOKENS
    assert service.temperature == TEMPERATURE_LLM

def test_generate_response():
    service = AiChatService(Model=ChatOpenAI, model_name=MODEL_NAME_LLM, api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Your are a helpful AI assistant for a phone shop. \nCONTEXT: Newest Iphone is Iphone 16 MAX."),
        ("user", "What is the newest Iphone?")
    ])
    prompt = prompt.invoke({})
    result = service.generate(prompt=prompt)
    print(result.content)
    assert isinstance(result.content, str) and len(result.content) > 0 and "Iphone 16 MAX".lower() in result.content.lower()