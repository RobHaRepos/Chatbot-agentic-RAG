from langchain_openai import ChatOpenAI
from app.services.llm import AiChatService
from app.config import MAX_TOKENS, TEMPERATURE_LLM

def test_build_prompt_default():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    question = "What is the newest Iphone?"
    context = "The newest Iphone is the Iphone 16 MAX."
    result = service.build_prompt(question=question, context=context)
    print(result)
    assert isinstance(result.messages, list) and len(result.messages) > 0 and question in result.messages and context in result.messages
    
def test_build_prompt_custom():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    question = "What is the newest Iphone?"
    context = "The newest Iphone is the Iphone 16 MAX."
    template = "Q: {question}\nA: {context}"
    result = service.build_prompt(question=question, context=context, template=template)
    
    assert isinstance(result, str) and len(result) > 0 and question in result and context in result
    
def test_generate_uses_define_llm():
    service = AiChatService(Model=ChatOpenAI, model_name="gpt-4.1-mini", api_key=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE_LLM)
    prompt = "What is the newest Iphone?"
    result = service.generate(prompt=prompt)
    assert isinstance(result, str) and len(result) > 0 and prompt in result