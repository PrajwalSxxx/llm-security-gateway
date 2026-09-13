import json
import math
import sqlite3
from pathlib import Path


class LocalRetriever:
    """Semantic local RAG using Ollama embeddings and SQLite as an embedded vector store."""

    def __init__(self, documents_dir: Path, provider, database_path: Path):
        self.documents_dir = documents_dir
        self.provider = provider
        self.database_path = database_path
        self._init_db()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id TEXT PRIMARY KEY, source TEXT NOT NULL, source_type TEXT NOT NULL,
                trust_level TEXT NOT NULL, text TEXT NOT NULL, embedding TEXT NOT NULL)""")

    def _chunks(self, text: str, size: int = 700, overlap: int = 100):
        start = 0
        while start < len(text):
            end = min(len(text), start + size)
            chunk = text[start:end].strip()
            if chunk:
                yield chunk
            if end == len(text):
                break
            start = end - overlap

    def index_documents(self, force: bool = False) -> int:
        files = sorted(self.documents_dir.glob("*"))
        files = [path for path in files if path.is_file() and path.suffix.lower() in {".txt", ".md"}]
        if force:
            with self._connect() as db:
                db.execute("DELETE FROM document_chunks")
        with self._connect() as db:
            existing = {row["chunk_id"] for row in db.execute("SELECT chunk_id FROM document_chunks")}
        pending = []
        for path in files:
            source = str(path.relative_to(self.documents_dir.parent)).replace("\\", "/")
            for number, text in enumerate(self._chunks(path.read_text(encoding="utf-8", errors="replace"))):
                chunk_id = f"{source}::chunk-{number}"
                if chunk_id not in existing:
                    pending.append((chunk_id, source, text))
        if pending:
            embeddings = self.provider.embed([item[2] for item in pending])
            if len(embeddings) != len(pending):
                raise RuntimeError("Local embedding model returned an unexpected number of vectors")
            with self._connect() as db:
                for (chunk_id, source, text), embedding in zip(pending, embeddings):
                    db.execute("INSERT OR REPLACE INTO document_chunks VALUES(?,?,?,?,?,?)",
                               (chunk_id, source, "external_document", "UNTRUSTED", text, json.dumps(embedding)))
        return len(existing) + len(pending)

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
        return sum(x * y for x, y in zip(left, right)) / denominator if denominator else 0.0

    def retrieve(self, query: str, requested: str | None = None, top_k: int = 3) -> dict:
        self.index_documents()
        query_embedding = self.provider.embed([query])[0]
        with self._connect() as db:
            rows = db.execute("SELECT * FROM document_chunks").fetchall()
        if requested:
            requested_name = Path(requested).name.lower()
            filtered = [row for row in rows if Path(row["source"]).name.lower() == requested_name]
            if filtered:
                rows = filtered
        if not rows:
            raise FileNotFoundError("No local documents are available")
        ranked = sorted(((self._cosine(query_embedding, json.loads(row["embedding"])), row) for row in rows),
                        key=lambda item: item[0], reverse=True)[:top_k]
        chunks = [{"chunk_id": row["chunk_id"], "source": row["source"], "source_type": row["source_type"],
                   "trust_level": row["trust_level"], "content": row["text"], "similarity": round(score, 4)}
                  for score, row in ranked]
        return {"source": chunks[0]["source"], "content": "\n\n".join(item["content"] for item in chunks),
                "chunks": chunks, "trust_label": "UNTRUSTED_EXTERNAL_CONTENT", "provenance": "RAG_DOCUMENT"}

    def status(self) -> dict:
        with self._connect() as db:
            count = db.execute("SELECT COUNT(*) AS count FROM document_chunks").fetchone()["count"]
        return {"vector_database": "SQLite local", "indexed_chunks": count, "embedding_model": self.provider.embedding_model}
