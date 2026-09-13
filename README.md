# Runtime Security and Threat Mitigation for Autonomous LLM Agents

This is a controlled local prototype showing how indirect prompt injection (IPI) can influence an agent through untrusted documents, and how a runtime security gateway can stop unsafe tool actions before execution.

## What It Demonstrates

- Mock agent planning and structured tool actions.
- Controlled `read_file`, `write_file`, `web_search`, `database_query`, and `http_request` tools.
- Vulnerable mode for research comparison and protected mode for enforcement.
- Untrusted-content labeling and local retrieval.
- Deterministic validation, intent/action comparison, IPI signals, sensitive-data detection, risk scoring, policy checks, and NetworkX TDG history.
- SQLite audit logs with a SHA-256 hash chain.
- FastAPI backend and Streamlit dashboard.
- A generated dataset of 50 benign and 50 malicious scenarios.

This project uses fake secrets, local documents, mock search/database/network tools, and sandbox path checks. It does not attack real services.

## Quick Start

## Download from GitHub

Install Git, then run:

```powershell
git clone https://github.com/PrajwalSxxx/llm-security-gateway.git
cd llm-security-gateway
```

The commands below create an isolated Python environment, install dependencies, and start the local application. Docker, PostgreSQL, Ollama, and API keys are not required for the default mock mode.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

In a second terminal:

```powershell
cd C:\Users\Prajwal\llm-runtime-security
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

Change `mode` to `VULNERABLE` to see the deliberately unsafe comparison path. `SAFE_MOCK` currently uses the same deterministic protected controls without external LLM calls.

## Evaluation and Tests

```powershell
pytest -q
python scripts\evaluate.py
```

The evaluation writes actual output to `reports/evaluation.json` and scenarios to `datasets/scenarios.json`. It measures detection, false positives, false negatives, and average processing latency from the local run.

## Architecture and Security Flow

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/USER_GUIDE.md](docs/USER_GUIDE.md), [docs/PROJECT_EXPLANATION.md](docs/PROJECT_EXPLANATION.md), and [docs/VIVA.md](docs/VIVA.md).

The core rule is: the agent proposes an action, but it never directly executes it. `SecurityGateway.evaluate()` runs before `tools.execute()`.

## Risk and Policy

Risk is an explainable experimental score from 0 to 100. Injection indicators, protected paths, external requests, sensitive patterns, intent mismatch, and dangerous action history add points. Thresholds and blocked resources are in `config/policies.yaml`. These values are not universal security standards.

## Limitations

The default planner is deterministic and mock-based, keyword IPI detection is incomplete, local retrieval is token-overlap rather than production embeddings, the HTTP tool is a mock, and SQLite is not a multi-user production audit store. Hash chaining detects ordinary modification but is not absolute tamper-proofing. A real deployment needs stronger isolation, authentication, secret management, content provenance, comprehensive policy testing, and independent monitoring.
