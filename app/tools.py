from pathlib import Path
from typing import Any

from .config import ALLOWED_FILE_ROOTS, SANDBOX
from .documents import extract_text, is_supported
from .models import ToolAction


def resolve_allowed_path(path: str) -> Path:
    root = SANDBOX.resolve()
    # Local models sometimes wrap a Windows path after a backslash.
    path = path.replace("\r", "").replace("\n", "").strip()
    if path.lower().startswith("sandbox-"):
        path = "documents/" + path[8:]
    candidate = Path(path).expanduser()
    target = candidate.resolve() if candidate.is_absolute() else (root / path).resolve()
    if len(Path(path).parts) == 1 and not target.exists():
        document_target = (root / "documents" / path).resolve()
        if document_target.exists() or not Path(path).suffix:
            target = document_target
    if not any(target == allowed or allowed in target.parents for allowed in ALLOWED_FILE_ROOTS):
        raise PermissionError("path is outside the configured allowed file roots")
    return target


def execute(action: ToolAction) -> dict[str, Any]:
    args = action.arguments
    if action.tool == "read_file":
        target = resolve_allowed_path(str(args["path"]))
        if not target.exists():
            raise FileNotFoundError(str(target))
        if not is_supported(target):
            raise ValueError(f"unsupported document type: {target.suffix or 'none'}")
        return {"text": extract_text(target), "path": str(target), "file_type": target.suffix.lower()}
    if action.tool == "write_file":
        target = resolve_allowed_path(str(args["path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(args.get("data", "")), encoding="utf-8")
        return {"written": str(target), "bytes": len(str(args.get("data", "")).encode())}
    if action.tool == "web_search":
        return {"results": [{"title": "Local mock result", "snippet": str(args.get("query", ""))}]}
    if action.tool == "database_query":
        return {"rows": [{"id": 1, "name": "simulated vendor", "status": "active"}]}
    if action.tool == "http_request":
        url = str(args.get("url", ""))
        return {"mock_request": {"method": args.get("method", "POST"), "url": url,
                                  "sent": True, "local_only": True,
                                  "actual_transport": "in-process simulation",
                                  "received_by": "simulated local service"}}
    raise ValueError(f"unknown tool: {action.tool}")
