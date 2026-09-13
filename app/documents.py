import csv
import json
import re
from pathlib import Path


SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json"}:
        if suffix == ".csv":
            with path.open(newline="", encoding="utf-8", errors="replace") as handle:
                return "\n".join(" | ".join(row) for row in csv.reader(handle))
        text = path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".json":
            try:
                return json.dumps(json.loads(text), indent=2)
            except json.JSONDecodeError:
                return text
        return text
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support requires the pypdf package") from exc
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX support requires the python-docx package") from exc
        return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
    raise ValueError(f"Unsupported document type: {suffix or 'none'}")


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_SUFFIXES


def extract_requested_path(request: str) -> str | None:
    patterns = [r"[A-Za-z]:\\[^\"\n]+?\.(?:pdf|docx|txt|md|csv|json)",
                r"(?:\.\.\\|\.\\)[^ \n,;]+",
                r"/[A-Za-z0-9_./ -]+\.(?:pdf|docx|txt|md|csv|json)"]
    match = next((re.search(pattern, request, re.IGNORECASE) for pattern in patterns if re.search(pattern, request, re.IGNORECASE)), None)
    return match.group(0).rstrip(".,;:)") if match else None
