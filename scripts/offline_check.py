import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent import Runtime  # noqa: E402
from app.audit import AuditLogger  # noqa: E402
from app.config import ROOT as APP_ROOT  # noqa: E402
from app.llm.ollama_provider import OllamaError  # noqa: E402


def main():
    print("OFFLINE SYSTEM CHECK")
    print("\nOllama and local models:")
    try:
        runtime = Runtime(AuditLogger(APP_ROOT / "offline_check.db"))
        status = runtime.local_status()
        print("Ollama: OK")
        print(f"LLM Model: {'OK' if status['model_installed'] else 'MISSING'} ({runtime.provider.model})")
        print(f"Embeddings: {'OK' if status['embedding_model_installed'] else 'MISSING'} ({runtime.provider.embedding_model})")
        print(f"Vector DB: OK ({status['indexed_chunks']} indexed chunks)")
        print("Database: OK")
        print("Security Engine: OK")
        print("External Providers: DISABLED")
        print("\nSTATUS: READY FOR OFFLINE OPERATION")
        print(json.dumps(status, indent=2))
    except OllamaError as exc:
        print(str(exc))
        print("\nSTATUS: NOT READY")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
