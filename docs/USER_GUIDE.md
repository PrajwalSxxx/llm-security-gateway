# Beginner User Guide

## 1. Open a terminal

Open PowerShell.

## 2. Navigate to the project

```powershell
cd C:\Users\Prajwal\llm-runtime-security
```

## 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Configure `.env`

```powershell
Copy-Item .env.example .env
```

The default `LLM_PROVIDER=ollama` uses the local model and needs no API key. Do not put real secrets in the sandbox.

## 5. Start services

Ollama must be installed and its local models must be available. Docker, PostgreSQL, and external services are not required.

## 6. Start the backend

```powershell
python run.py
```

Leave this terminal open. The API is at `http://127.0.0.1:8000`.

## 7. Start the dashboard

Open a second PowerShell window and run:

```powershell
cd C:\Users\Prajwal\llm-runtime-security
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\streamlit_app.py
```

## 8. Open the dashboard

Open `http://127.0.0.1:8501` in a browser.

## 9. Run a normal request

Select no document, choose `PROTECTED`, and enter `What is the capital of France?` for a normal local LLM answer. To test a local document operation, select `report.txt` and ask `Summarize report.txt.`.

## 10. Run a malicious document

Select `vendor_malicious.txt`, choose `PROTECTED`, and enter `Summarize vendor_malicious.txt.`. The content contains a fake instruction to access credentials and transmit them. The model-derived action must be blocked.

## 11. Compare modes

Run the same malicious document with `VULNERABLE`. This mode is intentionally unsafe and demonstrates tool attempts without the runtime gateway. Never use it with real resources.

## 12. Run evaluation

```powershell
python scripts\evaluate.py
```

Read the generated `reports\evaluation.json`. The script creates 50 benign and 50 malicious local scenarios and reports measured values.

## Useful API checks

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/audit/verify
```
