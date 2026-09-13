import json
from pathlib import Path
from typing import Any

from .config import SANDBOX
from .models import ToolAction


def _safe(path: str) -> Path:
    root = SANDBOX.resolve()
    target = (root / path).resolve()
    if root not in target.parents:
        raise PermissionError("path is outside the sandbox")
    return target


def execute(action: ToolAction) -> dict[str, Any]:
    args = action.arguments
    if action.tool == "read_file":
        target = _safe(str(args["path"]))
        if not target.exists():
            raise FileNotFoundError(str(target))
        return {"text": target.read_text(encoding="utf-8", errors="replace"), "path": str(target)}
    if action.tool == "write_file":
        target = _safe(str(args["path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(args.get("data", "")), encoding="utf-8")
        return {"written": str(target), "bytes": len(str(args.get("data", "")).encode())}
    if action.tool == "web_search":
        return {"results": [{"title": "Local mock result", "snippet": str(args.get("query", ""))}]}
    if action.tool == "database_query":
        return {"rows": [{"id": 1, "name": "simulated vendor", "status": "active"}]}
    if action.tool == "http_request":
        return {"mock_request": {"method": args.get("method", "POST"), "url": args.get("url"), "sent": True}}
    raise ValueError(f"unknown tool: {action.tool}")
