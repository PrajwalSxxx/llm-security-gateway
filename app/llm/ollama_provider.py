import json
from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaUnavailable(OllamaError):
    pass


class OllamaModelMissing(OllamaError):
    pass


class OllamaProvider:
    """Synchronous Ollama client restricted to the local endpoint."""

    def __init__(self, base_url: str, model: str, embedding_model: str, offline: bool = True, timeout: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embedding_model = embedding_model
        self.offline = offline
        self.timeout = timeout
        parsed = httpx.URL(self.base_url)
        if offline and parsed.host not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("OFFLINE_MODE requires Ollama to use localhost")

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(self.base_url + path, json=payload, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise OllamaUnavailable("OLLAMA IS NOT RUNNING\nStart Ollama and try again.") from exc
        if response.status_code == 404 and path in {"/api/chat", "/api/generate"}:
            raise OllamaModelMissing(f"MODEL NOT INSTALLED\nInstall the configured local model: {self.model}")
        if response.status_code >= 400:
            raise OllamaError(f"Ollama request failed ({response.status_code}): {response.text[:500]}")
        return response.json()

    def models(self) -> list[str]:
        try:
            response = httpx.get(self.base_url + "/api/tags", timeout=10)
            response.raise_for_status()
            return [item["name"] for item in response.json().get("models", [])]
        except httpx.HTTPError as exc:
            raise OllamaUnavailable("OLLAMA IS NOT RUNNING\nStart Ollama and try again.") from exc

    def check(self) -> dict[str, Any]:
        installed = self.models()
        return {"reachable": True, "model_installed": self.model in installed or any(name.startswith(self.model + ":") for name in installed),
                "embedding_model_installed": self.embedding_model in installed or any(name.startswith(self.embedding_model + ":") for name in installed),
                "models": installed, "endpoint": self.base_url}

    def generate(self, prompt: str, system: str = "") -> str:
        response = self._request("/api/generate", {"model": self.model, "prompt": prompt, "system": system, "stream": False,
                                                    "options": {"temperature": 0, "seed": 42}})
        return response.get("response", "")

    def chat(self, messages: list[dict[str, str]], system: str = "", response_format: dict[str, Any] | str | None = None) -> str:
        prepared = ([{"role": "system", "content": system}] if system else []) + messages
        payload: dict[str, Any] = {"model": self.model, "messages": prepared, "stream": False,
                                   "options": {"temperature": 0, "seed": 42}}
        if response_format is not None:
            payload["format"] = response_format
        response = self._request("/api/chat", payload)
        return response.get("message", {}).get("content", "")

    def structured_output(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        system = "Return only valid JSON. Follow this schema exactly: " + json.dumps(schema, separators=(",", ":"))
        text = self.chat(messages, system=system, response_format=schema)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise OllamaError(f"Malformed structured output from local model: {text[:500]}") from exc

    def tool_calling(self, messages: list[dict[str, str]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        schema = {"type": "object", "properties": {"action": {"type": "string", "enum": ["final", "tool"]},
                 "answer": {"type": "string"}, "tool": {"type": "string"}, "arguments": {"type": "object"}},
                 "required": ["action"]}
        prompt = messages + [{"role": "user", "content": "Available tools:\n" + json.dumps(tools) +
                              "\nChoose final or one tool. Never invent tools."}]
        return self.structured_output(prompt, schema)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._request("/api/embed", {"model": self.embedding_model, "input": texts})
        return response.get("embeddings", [])
