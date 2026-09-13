from typing import Any, Literal

from pydantic import BaseModel, Field


Decision = Literal["ALLOW", "BLOCK", "REQUIRE_APPROVAL"]


class ToolAction(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    source: str = "agent"
    provenance: str = "AGENT_GENERATED"
    capabilities: list[str] = Field(default_factory=list)
    data_class: str = "UNKNOWN"
    destination: str | None = None


class Intent(BaseModel):
    goal: str
    allowed_tools: list[str]
    allowed_operations: list[str]
    target_resources: list[str] = Field(default_factory=list)
    external_transmission: bool = False


class SecurityDecision(BaseModel):
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    reasons: list[str]
    signals: list[str] = Field(default_factory=list)
    intent: Intent
    action: ToolAction
    tdg_path: list[str] = Field(default_factory=list)
    risk_components: dict[str, int] = Field(default_factory=dict)
    policy_result: str = ""


class RequestInput(BaseModel):
    user_request: str
    content_path: str | None = None
    mode: Literal["PROTECTED", "VULNERABLE"] = "PROTECTED"
    session_id: str | None = None
    use_rag: bool = False
