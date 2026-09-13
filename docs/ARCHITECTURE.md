# Technical Architecture

## Data Flow

1. A user sends a request and optionally selects a local document.
2. `LocalRetriever` chunks local documents, embeds them with Ollama `nomic-embed-text`, stores vectors in SQLite, and labels retrieved chunks `UNTRUSTED_EXTERNAL_CONTENT`.
3. `RealLocalAgent` asks Ollama `qwen2.5:3b` for either a final answer or a structured `ToolAction`.
4. `SecurityGateway` validates the tool, infers user intent, detects injection and sensitive data, calculates risk, updates the TDG, and applies YAML policies.
5. Only an `ALLOW` decision reaches `tools.execute()`.
6. Every request and tool decision is written to SQLite with a chained SHA-256 digest.

## Components

- `app/models.py`: Pydantic action, intent, decision, and request schemas.
- `app/llm/`: Ollama-only local provider and structured output client.
- `app/agent.py`: local-model agent and baseline/protected orchestration.
- `app/security.py`: intent, IPI, sensitive data, risk, policy, and TDG logic.
- `app/tools.py`: sandbox-constrained tools; the network tool is mock-only.
- `app/rag.py`: local chunking, Ollama embeddings, SQLite vector search, and provenance.
- `app/audit.py`: SQLite events and tamper-evident hash chain.
- `app/main.py`: FastAPI endpoints.
- `dashboard/streamlit_app.py`: operator dashboard.

## Trust Boundaries

User input, retrieved documents, and agent proposals are untrusted. The gateway is outside the agent's authority. The sandbox is the only filesystem area tools can access. Protected files and external destinations are policy-controlled.

## Threat Model

The primary threat is an instruction embedded in a document that tries to override the user's goal and cause credential access or external transmission. The prototype also handles malformed/unknown tools, path traversal, sensitive output, and dangerous action sequences.

## RAG

The application uses no hosted retrieval service. Local chunks are embedded by `nomic-embed-text` through Ollama and stored as JSON vectors in SQLite. Cosine similarity selects top chunks, and each result carries source, source type, trust level, and chunk ID.

## Tool Dependency Graph

NetworkX records action labels. The dangerous sequence `untrusted -> credential_access -> external_transmission` raises risk to critical. The graph is session history in this prototype, not a universal causal proof.

## Risk and Policy

Scores are transparent experimental parameters. Policies in `config/policies.yaml` block credential/protected paths, unknown tools, unsafe paths, configured destinations, and sensitive external transmission. Scores over 80 block; scores from 61 to 80 require approval; lower scores can execute when intent and policy match.

## Audit Security

Each event includes the previous event hash and a digest over timestamp, session, type, payload, and previous hash. `GET /audit/verify` recomputes the chain. This makes offline modification detectable, but an attacker controlling the database and keyless verifier could still replace the entire log; production needs append-only storage and independent key management.
