import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "sandbox"
ALLOWED_FILE_ROOTS = [SANDBOX.resolve(), (Path.home() / "Documents").resolve(),
                      (Path.home() / "Desktop").resolve(), ROOT.resolve()]
POLICY_PATH = ROOT / "config" / "policies.yaml"
load_dotenv(ROOT / ".env")


def load_policies() -> dict:
    try:
        with POLICY_PATH.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"Unable to load policy configuration: {exc}") from exc


def setting(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def settings() -> dict:
    provider = setting("LLM_PROVIDER", "ollama").lower()
    return {
        "llm_provider": provider,
        "ollama_base_url": setting("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": setting("OLLAMA_MODEL", "qwen2.5:3b"),
        "embedding_model": setting("EMBEDDING_MODEL", "nomic-embed-text"),
        "offline_mode": setting("OFFLINE_MODE", "true").lower() in {"1", "true", "yes", "on"},
        "database_path": ROOT / "runtime_security.db",
        "vector_database_path": ROOT / "vector_store.db",
        "allowed_file_roots": [str(path) for path in ALLOWED_FILE_ROOTS],
    }
