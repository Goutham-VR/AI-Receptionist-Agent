import os

from app.providers.base import BaseLLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider

def get_llm_provider() -> BaseLLMProvider:
    provider_name = os.getenv(
    "LLM_PROVIDER",
    "gemini"
    ).lower()


    if provider_name == "gemini":
        return GeminiProvider()

    if provider_name == "groq":
        return GroqProvider()

    raise ValueError(
        f"Unsupported LLM provider: {provider_name}"
    )


def get_fallback_provider() -> BaseLLMProvider:
    provider_name = os.getenv(
    "LLM_PROVIDER",
    "gemini"
    ).lower()


    if provider_name == "gemini":
        return GroqProvider()

    if provider_name == "groq":
        return GeminiProvider()

    raise ValueError(
        f"Unsupported LLM provider: {provider_name}"
    )

