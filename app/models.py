from typing import Any, Literal

from pydantic import BaseModel, Field


Decision = Literal["ALLOW", "BLOCK", "REQUIRE_APPROVAL"]


class ToolAction(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    source: str = "agent"


class Intent(BaseModel):
    goal: str
    allowed_tools: list[str]
    allowed_operations: list[str]
    external_transmission: bool = False


class SecurityDecision(BaseModel):
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    reasons: list[str]
    signals: list[str] = Field(default_factory=list)
    intent: Intent
    action: ToolAction
    tdg_path: list[str] = Field(default_factory=list)


class RequestInput(BaseModel):
    user_request: str
    content_path: str | None = None
    mode: Literal["PROTECTED", "VULNERABLE", "SAFE_MOCK"] = "PROTECTED"
