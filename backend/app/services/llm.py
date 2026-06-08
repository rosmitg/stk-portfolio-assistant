from langchain_anthropic import ChatAnthropic

from app.core.config import settings


def get_llm(model: str = "claude-opus-4-8") -> ChatAnthropic:
    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )
