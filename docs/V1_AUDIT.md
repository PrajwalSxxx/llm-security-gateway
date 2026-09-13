# V1 Audit

| Component | Current implementation | Problem | Keep / Replace / Upgrade | Reason |
|---|---|---|---|---|
| Agent | `MockAgent` in `app/agent.py` | Always proposes a file read and derives attack calls with hard-coded string checks | Replace in production; keep as baseline | It is not an LLM agent and random questions trigger unrelated tools |
| LLM provider | None; `SAFE_MOCK` is deterministic | No local or remote model is called | Replace with `OllamaProvider` | The upgraded system must run against Ollama only |
| RAG | Token-overlap selection in `app/rag.py` | Not semantic and returns one whole document | Upgrade | Add local Ollama embeddings, chunking, provenance, and SQLite vector storage |
| Security gateway | `SecurityGateway` in `app/security.py` | Useful checks, but keyword-heavy and lacks capability/provenance models | Upgrade | Preserve deterministic enforcement while adding signal components |
| Intent engine | `infer_intent()` keyword rules | Limited goals and no target-resource representation | Upgrade | Structured intent must be compared with every model action |
| IPI detector | Fixed substring list | One signal cannot represent provenance, capability, or chain risk | Upgrade | Combine explainable signals without treating keywords as a solution |
| Sensitive data | Regex patterns in `app/security.py` | Useful baseline, but not attached to data classes | Upgrade | Add configurable data classes to actions and audit events |
| Risk engine | Inline score additions in gateway | No separate components or configurable weights | Upgrade | Expose injection, provenance, intent, tool, destination, TDG, and policy scores |
| Policy engine | `config/policies.yaml` | Basic allowed tools and paths | Upgrade | Add offline network policy, capabilities, and approval behavior |
| TDG | NetworkX label history | Tracks only short labels, not source/capability/data/destination | Upgrade | Record provenance-aware action nodes and dangerous sequences |
| Tools | `app/tools.py` | Sandbox file tools plus simulated HTTP/search/database | Keep and upgrade | Keep all resources local; add capabilities and local HTTP simulation |
| Audit | SQLite plus SHA-256 chain in `app/audit.py` | Hash chain works but event payload is incomplete | Upgrade | Include intent, provenance, capabilities, risk components, TDG, and execution |
| Database | SQLite audit database | Suitable for offline prototype | Keep | No service dependency is needed |
| API | FastAPI `/run`, audit, metrics | Runtime only supports mock flow | Upgrade | Add local LLM health, approvals, offline check, and real agent execution |
| Dashboard | Streamlit single-run view | Does not show local Ollama status or approval queue | Upgrade | Expose offline/local status, action details, and approval controls |
| Evaluation | Generated benign/malicious mock scenarios | Does not compare a real local LLM baseline with protected mode | Upgrade | Execute baseline and protected local model benchmarks |
| Tests | Five security unit tests | No provider, agent, RAG, or offline tests | Upgrade | Add local-provider mocks and end-to-end gateway tests |
| Configuration | `.env.example` includes unused cloud-era fields | No enforced offline/local provider | Replace/upgrade | Make Ollama and offline mode the only production configuration |
| Documentation | README, user, architecture, explanation, viva docs | Describes mock mode as the main implementation | Upgrade | Document V2 local architecture and offline operation |
| Docker | Dockerfile and Compose | Optional, not an offline model runtime | Keep with clarification | Ollama remains a host-local service; Docker is not required |

## Traced V1 Execution

`POST /run` creates a session in `app/main.py`, retrieves one text document, logs a request, and calls `MockAgent.propose()`. That method always creates a `read_file` action, even when a request is a normal question. It inspects document text for attack phrases and creates additional actions itself. In protected mode, each action goes to `SecurityGateway.evaluate()` before `tools.execute()`; in vulnerable mode, it bypasses the gateway. The V1 security boundary is real, but the model decision is not.
