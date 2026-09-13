import re
from pathlib import Path
from typing import Any

import networkx as nx

from .config import SANDBOX, load_policies
from .models import Intent, SecurityDecision, ToolAction


SENSITIVE_PATTERNS = {
    "API_KEY": r"(?i)\b(?:api[_ -]?key)\b\s*[:=]\s*[^\s]+",
    "PASSWORD": r"(?i)\bpassword\b\s*[:=]\s*[^\s]+",
    "TOKEN": r"(?i)\btoken\b\s*[:=]\s*[^\s]+",
    "SECRET": r"(?i)\bsecret\b\s*[:=]\s*[^\s]+",
    "PRIVATE_KEY": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "EMAIL": r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
}
INJECTION_TERMS = ("ignore previous", "system message", "developer instruction", "reveal secrets",
                   "send credentials", "upload this file", "override", "call http_request")


def detect_sensitive(text: str) -> list[str]:
    return [name for name, pattern in SENSITIVE_PATTERNS.items() if re.search(pattern, text)]


def detect_injection(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in INJECTION_TERMS if term in lowered]


def infer_intent(request: str) -> Intent:
    lower = request.lower()
    if any(word in lower for word in ("summarize", "read", "review")):
        return Intent(goal="document_summarization", allowed_tools=["read_file"], allowed_operations=["read"])
    if "search" in lower:
        return Intent(goal="web_search", allowed_tools=["web_search"], allowed_operations=["search"])
    if "write" in lower or "save" in lower:
        return Intent(goal="write_document", allowed_tools=["write_file"], allowed_operations=["write"])
    return Intent(goal="general_request", allowed_tools=[], allowed_operations=[])


def _is_secret_path(path: str) -> bool:
    lowered = path.lower().replace("\\", "/")
    return any(part in lowered for part in ("fake_secrets", ".env", "private", "credential"))


class SecurityGateway:
    def __init__(self, policies: dict | None = None):
        self.policies = policies or load_policies()
        self.graph = nx.DiGraph()
        self.history: list[str] = []

    def evaluate(self, request: str, action: ToolAction, external_content: str = "") -> SecurityDecision:
        intent = infer_intent(request)
        reasons: list[str] = []
        signals: list[str] = []
        score = 0
        tool = action.tool
        args = action.arguments
        path = str(args.get("path", ""))
        destination = str(args.get("url", args.get("destination", "")))
        content = external_content + " " + str(args.get("data", ""))
        injection = detect_injection(external_content)
        sensitive = detect_sensitive(content)
        if injection:
            signals.append("IPI indicators: " + ", ".join(injection))
            score += 20
        if tool not in self.policies.get("allowed_tools", []):
            reasons.append("Unknown or disallowed tool")
            score = max(score, 95)
        if path and _is_secret_path(path):
            reasons.append("Credential or protected path access")
            score += 55
        if path and not self._safe_path(path):
            reasons.append("Path escapes the controlled sandbox")
            score = max(score, 95)
        if tool == "write_file":
            score += 25
        if tool in ("http_request", "web_search"):
            score += 20
        if tool == "http_request" and destination and destination.startswith(("http://", "https://")):
            score += 25
        if sensitive:
            signals.append("Sensitive data: " + ", ".join(sensitive))
            score += 25
        if tool not in intent.allowed_tools:
            reasons.append("Action conflicts with user intent")
            score += 30
        if tool == "http_request" and sensitive:
            reasons.append("Sensitive data transmission is prohibited")
            score = max(score, 95)
        if tool == "http_request" and destination in self.policies.get("blocked_destinations", []):
            reasons.append("Destination is blocked by policy")
            score = max(score, 90)
        self._update_graph(tool, bool(injection), _is_secret_path(path), bool(tool == "http_request" and sensitive))
        if len(self.history) >= 3 and self.history[-3:] == ["untrusted", "credential_access", "external_transmission"]:
            reasons.append("Dangerous tool dependency chain detected")
            score = max(score, 95)
        if score > 0 and not reasons and injection:
            reasons.append("Suspicious instruction came from untrusted external content")
        score = min(100, score)
        threshold_block = int(self.policies.get("block_risk", 81))
        threshold_approval = int(self.policies.get("require_approval_risk", 61))
        decision = "BLOCK" if score >= threshold_block or reasons and any("prohibited" in r.lower() or "protected" in r.lower() for r in reasons) else "REQUIRE_APPROVAL" if score >= threshold_approval else "ALLOW"
        if decision == "ALLOW" and reasons:
            decision = "REQUIRE_APPROVAL"
        if decision == "ALLOW" and injection:
            decision = "REQUIRE_APPROVAL"
        return SecurityDecision(decision=decision, risk_score=score, reasons=reasons or ["Action matches intent and policy"],
                                signals=signals, intent=intent, action=action, tdg_path=list(self.history))

    def _safe_path(self, value: str) -> bool:
        try:
            candidate = (SANDBOX / value).resolve()
            return SANDBOX.resolve() in candidate.parents or candidate == SANDBOX.resolve()
        except OSError:
            return False

    def _update_graph(self, tool: str, untrusted: bool, credential: bool, external: bool):
        label = "external_transmission" if external else "credential_access" if credential else "untrusted" if untrusted else tool
        if self.history:
            self.graph.add_edge(self.history[-1], label)
        self.history.append(label)
        if len(self.history) > 10:
            self.history.pop(0)
