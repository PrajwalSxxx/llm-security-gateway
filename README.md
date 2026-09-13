# Runtime Security and Threat Mitigation for Autonomous LLM Agents

This is a controlled local prototype showing how indirect prompt injection (IPI) can influence an agent through untrusted documents, and how a runtime security gateway can stop unsafe tool actions before execution.

## What It Demonstrates

- Ollama local model planning and structured tool actions.
- Controlled `read_file`, `write_file`, `web_search`, `database_query`, and `http_request` tools.
- Vulnerable mode for research comparison and protected mode for enforcement.
- Semantic local RAG using Ollama embeddings and SQLite vector storage.
- Deterministic validation, intent/action comparison, IPI signals, sensitive-data detection, risk scoring, policy checks, and NetworkX TDG history.
- SQLite audit logs with a SHA-256 hash chain.
- FastAPI backend and Streamlit dashboard.
- A generated dataset of 50 benign and 50 malicious scenarios.

This project uses fake secrets, local documents, local mock search/database/network tools, and sandbox path checks. It does not attack real services. Normal operation requires only local Ollama, local models, local SQLite, and local application processes.

## Quick Start

## Download from GitHub

Install Git, then run:

```powershell
git clone https://github.com/PrajwalSxxx/llm-security-gateway.git
cd llm-security-gateway
```

The commands below create an isolated Python environment and install dependencies. Ollama and the two local models are required for normal operation; no API key is required.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
python run.py
```

In a second terminal:

```powershell
cd llm-security-gateway
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\streamlit_app.py
```

Open `http://127.0.0.1:8501`.

## API Examples

Protected legitimate request:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/run -ContentType 'application/json' -Body '{"user_request":"Read report.txt and summarize it.","content_path":"report.txt","mode":"PROTECTED"}'
```

Protected malicious document:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/run -ContentType 'application/json' -Body '{"user_request":"Summarize malicious_document.txt.","content_path":"malicious_document.txt","mode":"PROTECTED"}'
```

Change `mode` to `VULNERABLE` to compare the real local model without the runtime gateway. Its network operation remains an in-process simulation and never contacts the internet.

## Evaluation and Tests

```powershell
pytest -q
python scripts\offline_check.py
python scripts\evaluate.py
```

The evaluation writes actual output to `reports/evaluation_v2.json` and scenarios to `datasets/scenarios.json`. It executes the configured local model in baseline and protected modes and measures detection, false positives, false negatives, unauthorized calls, latency, and security overhead.

## Architecture and Security Flow

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md), [docs/OFFLINE_USER_GUIDE.md](docs/OFFLINE_USER_GUIDE.md), [docs/FINAL_DEMO_GUIDE.md](docs/FINAL_DEMO_GUIDE.md), [docs/V2_UPGRADE.md](docs/V2_UPGRADE.md), [docs/HOW_IT_WORKS_SIMPLE.md](docs/HOW_IT_WORKS_SIMPLE.md), [docs/PROJECT_EXPLANATION.md](docs/PROJECT_EXPLANATION.md), and [docs/VIVA.md](docs/VIVA.md).

The core rule is: the agent proposes an action, but it never directly executes it. `SecurityGateway.evaluate()` runs before `tools.execute()`.

## Risk and Policy

Risk is an explainable experimental score from 0 to 100. Injection indicators, protected paths, external requests, sensitive patterns, intent mismatch, and dangerous action history add points. Thresholds and blocked resources are in `config/policies.yaml`. These values are not universal security standards.

## Limitations

The local planner depends on model behavior, IPI detection is incomplete, the vector store is a simple SQLite embedded store, network/database tools are local simulations, and SQLite is not a multi-user production audit store. Hash chaining detects ordinary modification but is not absolute tamper-proofing. A real deployment needs stronger isolation, authentication, secret management, comprehensive policy testing, and independent monitoring.
