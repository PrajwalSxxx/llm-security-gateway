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

The default `LLM_PROVIDER=mock` needs no API key. Do not put real secrets in the sandbox.

## 5. Start services

No Docker, PostgreSQL, Ollama, or external service is required for the default mode.

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

Select `report.txt`, choose `PROTECTED`, and enter `Read report.txt and summarize it.`. The file read should be allowed.

## 10. Run a malicious document

Select `malicious_document.txt`, choose `PROTECTED`, and enter `Summarize malicious_document.txt.`. The content contains a fake instruction to read credentials and transmit them. The credential action must be blocked.

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
