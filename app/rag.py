import re
from pathlib import Path


class LocalRetriever:
    """Dependency-free TF-style token retrieval for controlled documents."""

    def __init__(self, documents_dir: Path):
        self.documents_dir = documents_dir

    def retrieve(self, query: str, requested: str | None = None) -> dict:
        candidates = list(self.documents_dir.glob("*.txt"))
        if requested:
            candidate = self.documents_dir / Path(requested).name
            if candidate.exists():
                candidates = [candidate]
        query_words = set(re.findall(r"[a-z0-9_]+", query.lower()))
        scored = []
        for path in candidates:
            text = path.read_text(encoding="utf-8", errors="replace")
            words = set(re.findall(r"[a-z0-9_]+", text.lower()))
            scored.append((len(query_words & words), path, text))
        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored:
            raise FileNotFoundError("No documents are available")
        score, path, text = scored[0]
        return {"source": str(path.relative_to(self.documents_dir.parent)),
                "content": text, "similarity": score, "trust_label": "UNTRUSTED_EXTERNAL_CONTENT"}
