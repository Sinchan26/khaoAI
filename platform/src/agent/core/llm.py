import os
from langchain_openai import ChatOpenAI
from .config import settings

def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "dummy-key-for-init")
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=temperature,
        api_key=api_key,
        max_tokens=800
    )
