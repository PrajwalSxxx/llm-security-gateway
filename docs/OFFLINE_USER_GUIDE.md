# Offline User Guide

## One-Time Setup

Internet is allowed only for installation and model download.

```powershell
cd C:\Users\Prajwal\llm-runtime-security
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Install Ollama and download the models:

```powershell
winget install --id Ollama.Ollama --exact
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

## After Setup

Disconnect the computer from the internet. Ollama must remain running locally.

Verify readiness:

```powershell
python scripts\offline_check.py
```

## Start

Terminal 1:

```powershell
ollama serve
```

If the Ollama desktop application is already running, do not start a second server.

Terminal 2:

```powershell
cd C:\Users\Prajwal\llm-runtime-security
.\.venv\Scripts\Activate.ps1
python run.py
```

Terminal 3:

```powershell
cd C:\Users\Prajwal\llm-runtime-security
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\streamlit_app.py
```

Open `http://127.0.0.1:8501`.

## Offline Demonstrations

Normal chat: enter `What is the capital of France?` with no document.

Local RAG: enable local semantic RAG and ask `What is the company leave policy?`.

Protected attack: choose `vendor_malicious.txt`, select `PROTECTED`, and ask `Summarize vendor_malicious.txt.`.

Baseline comparison: repeat with `VULNERABLE`. The HTTP operation is only an in-process mock and never sends data to the internet.

## Tests and Evaluation

```powershell
pytest -q
python scripts\offline_check.py
python scripts\evaluate.py
```

## Stop

Press `Ctrl+C` in the API and dashboard terminals. Stop Ollama from its desktop application, or use `Ctrl+C` if it was started with `ollama serve`.

## Troubleshooting

`OLLAMA IS NOT RUNNING`: start the Ollama desktop application or run `ollama serve`.

`MODEL NOT INSTALLED`: run `ollama pull qwen2.5:3b` and `ollama pull nomic-embed-text` while temporarily online.

Port `11434` unavailable: check the existing Ollama process; do not expose it publicly.

Vector database error: remove the local ignored `vector_store.db` and rerun the offline check to rebuild embeddings.

Database error: check that the project directory is writable.

Docker unavailable: Docker is optional; the default path uses local Windows processes and SQLite.
