import re
from pathlib import Path
import networkx as nx

from .config import SANDBOX, load_policies
from .models import Intent, SecurityDecision, ToolAction
from .tools import resolve_allowed_path


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
TOOL_CAPABILITIES = {
    "read_file": {"capabilities": ["READ_FILE"], "data_class": "PUBLIC_DOCUMENT", "risk": 10},
    "write_file": {"capabilities": ["WRITE_FILE"], "data_class": "LOCAL_OUTPUT", "risk": 40},
    "web_search": {"capabilities": ["LOCAL_SEARCH"], "data_class": "PUBLIC_DOCUMENT", "risk": 20},
    "database_query": {"capabilities": ["READ_DATABASE"], "data_class": "LOCAL_DATABASE", "risk": 25},
    "http_request": {"capabilities": ["EXTERNAL_NETWORK"], "data_class": "SENSITIVE_OR_PUBLIC", "risk": 50},
}


def detect_sensitive(text: str) -> list[str]:
    return [name for name, pattern in SENSITIVE_PATTERNS.items() if re.search(pattern, text)]


def detect_injection(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in INJECTION_TERMS if term in lowered]


def validate_action(action: ToolAction) -> list[str]:
    required = {"read_file": ("path",), "write_file": ("path",), "web_search": ("query",),
                "database_query": ("query",), "http_request": ("url",)}
    if action.tool not in required:
        return ["Unknown tool name"]
    errors = [f"Missing required argument: {name}" for name in required[action.tool] if name not in action.arguments]
    if "path" in action.arguments and not isinstance(action.arguments["path"], str):
        errors.append("path must be a string")
    if "url" in action.arguments and not isinstance(action.arguments["url"], str):
        errors.append("url must be a string")
    return errors


def infer_intent(request: str) -> Intent:
    lower = request.lower()
    wants_write = "write" in lower or "save" in lower
    if any(word in lower for word in ("summarize", "read", "review")):
        if wants_write:
            return Intent(goal="document_summarization_and_save", allowed_tools=["read_file", "write_file"],
                          allowed_operations=["read", "write"], target_resources=["requested_document", "requested_output"])
        return Intent(goal="document_summarization", allowed_tools=["read_file"], allowed_operations=["read"], target_resources=["requested_document"])
    if "search" in lower:
        return Intent(goal="web_search", allowed_tools=["web_search"], allowed_operations=["search"], target_resources=["local_search"])
    if "write" in lower or "save" in lower:
        return Intent(goal="write_document", allowed_tools=["write_file"], allowed_operations=["write"], target_resources=["requested_output"])
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
        components: dict[str, int] = {}
        weights = self.policies.get("risk_weights", {})
        tool = action.tool
        args = action.arguments
        path = str(args.get("path", ""))
        destination = str(args.get("url", args.get("destination", "")))
        content = external_content + " " + str(args.get("data", ""))
        validation_errors = validate_action(action)
        if validation_errors:
            reasons.extend(validation_errors)
            components["policy_risk"] = 100
            score = 100
        injection = detect_injection(external_content)
        sensitive = detect_sensitive(content)
        if injection:
            signals.append("IPI indicators: " + ", ".join(injection))
            components["injection_risk"] = int(weights.get("injection", 20))
            score += components["injection_risk"]
        if action.provenance in {"RAG_DOCUMENT", "UNTRUSTED_DOCUMENT", "EMAIL", "WEB_CONTENT_SIMULATION"}:
            components["provenance_risk"] = int(weights.get("provenance", 10))
            score += components["provenance_risk"]
            signals.append(f"Untrusted provenance: {action.provenance}")
        capability = TOOL_CAPABILITIES.get(tool)
        if capability:
            action.capabilities = action.capabilities or capability["capabilities"]
            action.data_class = action.data_class if action.data_class != "UNKNOWN" else capability["data_class"]
            components["tool_risk"] = capability["risk"]
            score += components["tool_risk"]
        if tool not in self.policies.get("allowed_tools", []):
            reasons.append("Unknown or disallowed tool")
            components["policy_risk"] = 95
            score = max(score, components["policy_risk"])
        if path and _is_secret_path(path):
            reasons.append("Credential or protected path access")
            components["sensitive_data_risk"] = int(weights.get("protected_path", 55))
            score += components["sensitive_data_risk"]
        if path and not self._safe_path(path):
            reasons.append("Path escapes the configured allowed file roots")
            components["policy_risk"] = max(components.get("policy_risk", 0), 95)
            score = max(score, 95)
        if tool == "write_file":
            components["write_risk"] = 25
            score += components["write_risk"]
        if tool == "http_request" and destination and not destination.startswith(("http://localhost", "http://127.0.0.1", "http://[::1]")):
            reasons.append("External destination is disabled in offline mode")
            components["destination_risk"] = int(weights.get("destination", 40))
            score += components["destination_risk"]
        if sensitive:
            signals.append("Sensitive data: " + ", ".join(sensitive))
            components["sensitive_data_risk"] = max(components.get("sensitive_data_risk", 0), int(weights.get("sensitive_data", 25)))
            score += 25
        if tool not in intent.allowed_tools:
            reasons.append("Action conflicts with user intent")
            components["intent_mismatch"] = int(weights.get("intent_mismatch", 30))
            score += components["intent_mismatch"]
        if tool == "http_request" and sensitive:
            reasons.append("Sensitive data transmission is prohibited")
            components["policy_risk"] = max(components.get("policy_risk", 0), 95)
            score = max(score, 95)
        if tool == "http_request" and destination in self.policies.get("blocked_destinations", []):
            reasons.append("Destination is blocked by policy")
            components["policy_risk"] = max(components.get("policy_risk", 0), 90)
            score = max(score, 90)
        self._update_graph(tool, bool(injection), _is_secret_path(path), bool(tool == "http_request" and sensitive))
        if len(self.history) >= 3 and self.history[-3:] == ["untrusted", "credential_access", "external_transmission"]:
            reasons.append("Dangerous tool dependency chain detected")
            components["tdg_risk"] = int(weights.get("tdg", 95))
            score = max(score, components["tdg_risk"])
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
                                signals=signals, intent=intent, action=action, tdg_path=list(self.history),
                                risk_components=components, policy_result=decision)

    def _safe_path(self, value: str) -> bool:
        try:
            resolve_allowed_path(value)
            return True
        except (OSError, PermissionError):
            return False

    def _update_graph(self, tool: str, untrusted: bool, credential: bool, external: bool):
        label = "external_transmission" if external else "credential_access" if credential else "untrusted" if untrusted else tool
        if self.history:
            self.graph.add_edge(self.history[-1], label)
        self.history.append(label)
        if len(self.history) > 10:
            self.history.pop(0)
