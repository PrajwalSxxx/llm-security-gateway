from pathlib import Path

from fastapi import FastAPI, HTTPException

from .agent import Runtime
from .audit import AuditLogger
from .config import ROOT
from .models import RequestInput
from .rag import LocalRetriever


runtime = Runtime(AuditLogger(ROOT / "runtime_security.db"), LocalRetriever(ROOT / "sandbox" / "documents"))
app = FastAPI(title="LLM Runtime Security Gateway", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "local-mock"}


@app.post("/run")
def run(request: RequestInput):
    try:
        return runtime.run(request)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
