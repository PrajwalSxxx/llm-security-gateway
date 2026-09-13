# V2 Upgrade

## Changed

- Installed Ollama locally and selected `qwen2.5:3b` for the RTX 2050 4 GB / 15.73 GB RAM machine.
- Added `OllamaProvider` using only `http://localhost:11434`.
- Added `nomic-embed-text` through Ollama for local embeddings.
- Replaced the production mock planner with `RealLocalAgent`.
- Kept `MockAgent` only as legacy reference code; baseline mode uses the real local model without the gateway.
- Added semantic chunking, local Ollama embeddings, provenance metadata, and SQLite vector storage.
- Added action validation, capability metadata, provenance-aware risk components, approval storage, and offline network policy.
- Added company-policy and malicious-document demonstrations.
- Added `/local-status`, `/approve/{session_id}`, and `scripts/offline_check.py`.
- Updated dashboard to show local/Ollama/offline status, cumulative metrics, provenance, risk components, TDG, and approval controls.

## Retained

The original FastAPI, Streamlit, SQLite audit database, SHA-256 chain, NetworkX graph, sandbox tools, YAML policies, tests, and documentation structure were retained and upgraded.

## Removed From Production

No OpenAI, Gemini, Anthropic, OpenRouter, hosted embeddings, or cloud database path is used. The old `mock` provider configuration was removed from `.env.example` and the local `.env` was updated to Ollama.

## Execution Now

The local model proposes either a final answer or structured JSON tool action. Every action is validated and evaluated by the gateway before the tool layer. Baseline mode intentionally omits this gateway for controlled comparison; its HTTP tool is still an in-process simulation and never contacts the internet.
