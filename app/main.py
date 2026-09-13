from fastapi import FastAPI, HTTPException

from .agent import Runtime
from .audit import AuditLogger
from .config import ROOT
from .llm.ollama_provider import OllamaError
from .models import RequestInput


runtime = Runtime(AuditLogger(ROOT / "runtime_security.db"))
app = FastAPI(title="Offline LLM Runtime Security Gateway", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "provider": "Ollama", "connection": "LOCAL", "offline_mode": runtime.settings["offline_mode"]}


@app.post("/run")
def run(request: RequestInput):
    try:
        return runtime.run(request)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/approve/{session_id}")
def approve(session_id: str):
    try:
        return runtime.approve(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/local-status")
def local_status():
    try:
        return runtime.local_status()
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/audit")
def audit(limit: int = 50):
    return {"events": runtime.audit.recent(limit)}


@app.get("/audit/verify")
def verify_audit():
    valid, message = runtime.audit.verify()
    return {"valid": valid, "message": message}


@app.get("/metrics")
def metrics():
    return runtime.audit.metrics()
