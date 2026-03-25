from app.providers.base import BaseProviderAdapter
from app.providers.ollama import OllamaAdapter
from app.providers.openai import OpenAIAdapter

def get_provider_adapter(provider: str) -> BaseProviderAdapter:
    if provider == "ollama":
        return OllamaAdapter()
    if provider in {"openai", "openai_compatible"}:
        return OpenAIAdapter()
    
    raise ValueError(f"Unsupported Provider: {provider}")