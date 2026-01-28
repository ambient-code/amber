"""State models for Amber LangGraph agent"""

from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

ConstitutionStatus = Literal["pass", "fail", "warning"]
OperatingMode = Literal["on-demand", "background", "scheduled", "webhook"]
AutonomyLevel = Literal[1, 2, 3, 4]
Phase = Literal[
    "pending",
    "analyzing",
    "implementing",
    "testing",
    "reviewing",
    "completed",
    "failed",
]


@dataclass
class ConstitutionCheck:
    """Track constitution compliance for a specific check"""

    principle: str
    status: ConstitutionStatus
    details: str
    file_references: list[str] = field(default_factory=list)


@dataclass
class Finding:
    """A single analysis finding"""

    category: str  # bug, security, performance, maintainability, etc.
    severity: Literal["critical", "high", "medium", "low"]
    title: str
    description: str
    file_path: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    recommendation: str | None = None


@dataclass
class Recommendation:
    """An actionable recommendation"""

    title: str
    description: str
    priority: Literal["P0", "P1", "P2", "P3"]
    effort: Literal["low", "medium", "high"]
    suggested_owner: str | None = None


@dataclass
class RiskAssessment:
    """Risk assessment for proposed changes"""

    severity: Literal["low", "medium", "high", "critical"]
    blast_radius: str
    rollback_complexity: Literal["trivial", "simple", "moderate", "complex"]
    details: str


class AmberState(TypedDict, total=False):
    """Core state passed through all graph nodes"""

    # Input context
    mode: OperatingMode
    trigger: dict[str, Any]

    # Session management
    session_id: str
    project_name: str
    repositories: list[str]

    # Workflow state
    current_phase: Phase
    autonomy_level: AutonomyLevel
    confidence: float  # 0.0 to 1.0

    # Analysis results
    findings: list[Finding]
    recommendations: list[Recommendation]
    risk_assessment: RiskAssessment | None

    # Actions taken
    branches_created: list[str]
    prs_created: list[str]
    comments_posted: list[str]

    # Safety and transparency
    plan: dict[str, Any]
    rollback_instructions: list[str]
    human_review_required: bool

    # Context management
    messages: Annotated[list[BaseMessage], add_messages]
    tool_results: list[dict[str, Any]]
    token_count: int

    # Constitution compliance
    constitution_checks: list[ConstitutionCheck]
    violations_detected: list[ConstitutionCheck]

    # Testing and validation
    tests_passed: bool
    linters_passed: bool

    # Follow-up handling
    followup_needed: bool

    # Error tracking
    errors: list[str]
