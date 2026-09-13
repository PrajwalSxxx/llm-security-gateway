import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class AuditLogger:
    """SQLite audit log with a SHA-256 chain. This is tamper-evident, not tamper-proof."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()
        self._init_db()

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL, event TEXT NOT NULL, payload TEXT NOT NULL,
                previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL)""")

    def log(self, session_id: str, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        clean = json.loads(json.dumps(payload, default=str))
        with self.lock, self._connect() as db:
            row = db.execute("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1").fetchone()
            previous = row["event_hash"] if row else "GENESIS"
            body = json.dumps({"timestamp": timestamp, "session_id": session_id,
                               "event": event, "payload": clean, "previous_hash": previous},
                              sort_keys=True, separators=(",", ":"))
            event_hash = hashlib.sha256(body.encode()).hexdigest()
            db.execute("INSERT INTO audit_events(timestamp,session_id,event,payload,previous_hash,event_hash) VALUES(?,?,?,?,?,?)",
                       (timestamp, session_id, event, json.dumps(clean), previous, event_hash))
        return {"timestamp": timestamp, "event": event, "payload": clean, "event_hash": event_hash}

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def metrics(self) -> dict[str, float | int]:
        with self._connect() as db:
            requests = db.execute("SELECT COUNT(*) AS count FROM audit_events WHERE event='request'").fetchone()["count"]
            decisions = db.execute("SELECT payload FROM audit_events WHERE event='tool_decision'").fetchall()
        total = allowed = blocked = high_risk = 0
        risk_total = 0
        for row in decisions:
            payload = json.loads(row["payload"])
            decision = payload.get("decision", {})
            risk = int(decision.get("risk_score", 0))
            total += 1
            risk_total += risk
            allowed += decision.get("decision") == "ALLOW"
            blocked += decision.get("decision") == "BLOCK"
            high_risk += risk >= 61
        return {"total_requests": requests, "total_tool_calls": total, "threats_detected": high_risk,
                "actions_blocked": blocked, "actions_allowed": allowed,
                "high_risk_actions": high_risk, "average_risk_score": round(risk_total / total, 2) if total else 0}

    def verify(self) -> tuple[bool, str]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY id").fetchall()
        previous = "GENESIS"
        for row in rows:
            payload = json.loads(row["payload"])
            body = json.dumps({"timestamp": row["timestamp"], "session_id": row["session_id"],
                               "event": row["event"], "payload": payload,
                               "previous_hash": previous}, sort_keys=True, separators=(",", ":"))
            expected = hashlib.sha256(body.encode()).hexdigest()
            if row["previous_hash"] != previous or row["event_hash"] != expected:
                return False, f"tampering detected at event {row['id']}"
            previous = row["event_hash"]
        return True, "audit chain verified"
