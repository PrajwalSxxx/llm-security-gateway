# How To Use

## One-Time Setup

```powershell
cd C:\Users\Prajwal\llm-runtime-security
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

## Start Ollama

```powershell
ollama serve
```

If the Ollama desktop application is already running, leave it running and do not start a second server.

## Verify the Model

```powershell
ollama list
python scripts\offline_check.py
```

## Start the Backend

```powershell
python run.py
```

The API is available at `http://127.0.0.1:8000`.

## Start the Dashboard

Open a second terminal:

```powershell
cd C:\Users\Prajwal\llm-runtime-security
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\streamlit_app.py
```

Open `http://127.0.0.1:8501`.

## Ask a Normal Question

Open **Agent Console** and enter:

```text
What is the difference between authentication and authorization?
```

No unrelated tool should be called.

## Read a Local File

The application accepts Windows paths inside the configured roots:

```text
Read C:\Users\Prajwal\llm-runtime-security\sandbox\documents\report.txt and summarize the methodology.
```

Allowed default roots are the project directory, its sandbox, the current user's Documents directory, and Desktop. Sensitive paths are still blocked.

Supported formats include `.txt`, `.md`, `.pdf`, `.docx`, `.csv`, and `.json`.

## Run Local RAG

Open **RAG Explorer**, enter:

```text
What is the company leave policy?
```

The system retrieves local chunks using `nomic-embed-text` and displays source, trust level, chunk ID, and similarity.

## Run the Attack Simulator

Open **Attack Simulator**, choose `Malicious vendor document`, select `PROTECTED`, and click **RUN ATTACK**. The model-derived network action should be blocked.

Repeat with `VULNERABLE` to see the baseline execute only the in-process mock tool.

## View Audit Data

Open **Audit Explorer** to search the recent local events and verify the hash chain.

The API equivalent is:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/audit/verify
```

## Run Evaluation

```powershell
python scripts\evaluate.py
```

Open **Evaluation** in the dashboard or inspect `reports\evaluation_v2.json`.

## Stop

Press `Ctrl+C` in the FastAPI, Streamlit, and `ollama serve` terminals.
