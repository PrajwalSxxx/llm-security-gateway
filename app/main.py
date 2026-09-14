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


@app.get("/tdg")
def tdg():
    return {"nodes": list(runtime.gateway.graph.nodes),
            "edges":[{"source": source, "target": target} for source, target in runtime.gateway.graph.edges]}


@app.get("/rag/status")
def rag_status():
    return runtime.retriever.status()


@app.get("/policies")
def policies():
    return runtime.gateway.policies


@app.get("/evaluation")
def evaluation():
    report = ROOT / "reports" / "evaluation_v2.json"
    if not report.exists():
        return {"available": False, "message": "Run python scripts/evaluate.py first"}
    import json
    return {"available": True, "report": json.loads(report.read_text(encoding="utf-8"))}


@app.get("/documents")
def documents():
    from .documents import is_supported
    directory = ROOT / "sandbox" / "documents"
    return {"documents": [{"path": str(path.relative_to(ROOT / "sandbox")).replace("\\", "/"),
                           "name": path.name, "suffix": path.suffix.lower(), "size": path.stat().st_size,
                           "indexed": is_supported(path)}
                          for path in sorted(directory.rglob("*")) if path.is_file()]}
