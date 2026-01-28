"""Tests for state models"""

import pytest

from amber.models import (
    AmberState,
    ConstitutionCheck,
    Finding,
    Recommendation,
    RiskAssessment,
)


def test_constitution_check_creation():
    """Test ConstitutionCheck dataclass"""
    check = ConstitutionCheck(
        principle="III - Type Safety",
        status="fail",
        details="panic() usage detected",
        file_references=["src/main.go:42"],
    )

    assert check.principle == "III - Type Safety"
    assert check.status == "fail"
    assert len(check.file_references) == 1


def test_finding_creation():
    """Test Finding dataclass"""
    finding = Finding(
        category="security",
        severity="high",
        title="Token logging detected",
        description="Service logs API token in plaintext",
        file_path="src/auth.go",
        line_number=123,
    )

    assert finding.category == "security"
    assert finding.severity == "high"
    assert finding.line_number == 123


def test_recommendation_creation():
    """Test Recommendation dataclass"""
    rec = Recommendation(
        title="Upgrade dependencies",
        description="Update kubernetes client to v0.35.0",
        priority="P1",
        effort="medium",
        suggested_owner="backend-team",
    )

    assert rec.priority == "P1"
    assert rec.effort == "medium"


def test_risk_assessment_creation():
    """Test RiskAssessment dataclass"""
    risk = RiskAssessment(
        severity="low",
        blast_radius="Single component",
        rollback_complexity="trivial",
        details="Changes isolated to handler",
    )

    assert risk.severity == "low"
    assert risk.rollback_complexity == "trivial"


def test_amber_state_initialization():
    """Test AmberState TypedDict"""
    state: AmberState = {
        "mode": "on-demand",
        "trigger": {"query": "test"},
        "session_id": "test-123",
        "project_name": "platform",
        "repositories": ["https://github.com/test/repo"],
        "messages": [],
        "findings": [],
        "current_phase": "pending",
        "autonomy_level": 2,
        "confidence": 0.8,
    }

    assert state["mode"] == "on-demand"
    assert state["confidence"] == 0.8
    assert state["autonomy_level"] == 2


def test_amber_state_optional_fields():
    """Test AmberState with minimal fields"""
    state: AmberState = {
        "session_id": "test-456",
        "project_name": "test-project",
    }

    assert state["session_id"] == "test-456"
    assert "findings" not in state  # Optional field not set
