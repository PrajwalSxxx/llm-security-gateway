from .ollama_provider import OllamaProvider


def build_provider(settings) -> OllamaProvider:
    provider = settings.get("llm_provider", "ollama").lower()
    if provider != "ollama":
        raise RuntimeError("Only the local Ollama provider is supported. Cloud providers are disabled.")
    return OllamaProvider(settings["ollama_base_url"], settings["ollama_model"], settings["embedding_model"], settings["offline_mode"])
