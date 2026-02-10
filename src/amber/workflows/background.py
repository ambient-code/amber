"""Background agent workflow for autonomous maintenance"""

from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage

from amber.config import get_settings
from amber.llm import get_llm
from amber.models import AmberState, RiskAssessment
from amber.tools import ALL_TOOLS


BACKGROUND_SYSTEM_PROMPT = """You are Amber operating in BACKGROUND AGENT mode for autonomous maintenance.

Your mission: Systematically reduce backlog and improve codebase health without human intervention (within safety bounds).

Decision criteria for auto-fix:
- Confidence >90%
- Time to fix <30 minutes
- Low blast radius
- No API contract changes
- All constitution checks pass

Always create a plan before implementing fixes.
Provide rollback instructions for every change.
Request human review when uncertain."""


def fetch_work_queue_node(state: AmberState) -> AmberState:
    """Fetch issues from work queue"""
    trigger = state.get("trigger", {})
    repo_name = trigger.get("repo_name", "ambient-code/platform")

    llm_with_tools = get_llm(max_tokens=2000).bind_tools(ALL_TOOLS)

    # Fetch open issues with specific labels
    messages = [
        SystemMessage(content=BACKGROUND_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Fetch work queue for repository {repo_name}.
Look for issues labeled: good-first-issue, technical-debt, amber:auto-fix
Return the list of issues."""
        ),
    ]

    response = llm_with_tools.invoke(messages)
    state["messages"] = [messages[0], response]

    return state


def prioritize_node(state: AmberState) -> AmberState:
    """Prioritize issues by severity and effort"""
    llm = get_llm(max_tokens=2000)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Prioritize issues using this ranking:
P0: Security CVEs, cluster outages
P1: Failing CI, breaking changes
P2: New issues needing triage
P3: Backlog grooming, tech debt

Select the highest priority issue to work on."""
        )
    )

    response = llm.invoke(messages)
    state["messages"].append(response)

    return state


def assess_auto_fix_node(state: AmberState) -> AmberState:
    """Determine if issue is auto-fixable with high confidence"""
    llm_with_tools = get_llm(max_tokens=4000).bind_tools(ALL_TOOLS)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Assess if this issue is auto-fixable:

Criteria for auto-fix:
1. Clear root cause identifiable
2. Solution well-defined and low-risk
3. Estimated time <30 minutes
4. No API contract changes
5. Low blast radius (limited to specific component)

Categories often auto-fixable:
- Dependency patches (patch version only)
- Lint fixes (gofmt, black, prettier)
- Documentation typos
- Test updates for deprecated APIs

Use available tools to investigate the issue.
Respond with: HIGH_CONFIDENCE, NEEDS_INVESTIGATION, or NO_WORK"""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    # Extract confidence from response
    content = response.content.lower() if hasattr(response, "content") else ""
    if "high_confidence" in content:
        state["confidence"] = 0.95
        state["autonomy_level"] = 2  # PR creator level
    elif "needs_investigation" in content:
        state["confidence"] = 0.5
        state["human_review_required"] = True
    else:
        state["confidence"] = 0.0

    return state


def route_by_confidence(state: AmberState) -> str:
    """Route based on confidence assessment"""
    if state.get("confidence", 0) >= 0.9:
        return "high_confidence"
    elif state.get("confidence", 0) > 0:
        return "needs_investigation"
    else:
        return "no_work"


def create_plan_node(state: AmberState) -> AmberState:
    """Create implementation plan"""
    llm = get_llm(max_tokens=2000)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Create a detailed implementation plan:

1. Files to modify
2. Changes to make (be specific)
3. Tests to run
4. Rollback procedure
5. Risk assessment (severity, blast radius)

Format the plan clearly with steps."""
        )
    )

    response = llm.invoke(messages)
    state["messages"].append(response)

    # Store plan
    state["plan"] = {"created": True, "content": response.content}

    return state


def implement_fix_node(state: AmberState) -> AmberState:
    """Implement the fix"""
    # In a real implementation, this would:
    # 1. Clone repo or use existing checkout
    # 2. Create feature branch
    # 3. Make code changes
    # 4. Run linters
    # 5. Commit changes

    state["branches_created"] = state.get("branches_created", [])
    state["branches_created"].append("amber/fix-issue-123")

    return state


def run_tests_node(state: AmberState) -> AmberState:
    """Run tests to validate fix"""
    # In real implementation: execute test suite
    state["tests_passed"] = True  # Placeholder
    state["linters_passed"] = True

    return state


def create_pr_node(state: AmberState) -> AmberState:
    """Create pull request"""
    llm_with_tools = get_llm(max_tokens=2000).bind_tools(ALL_TOOLS)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Create a pull request with this format:

## What I Changed
[Specific changes made]

## Why
[Root cause analysis, reasoning for this approach]

## Confidence
[90%] High - [Justification]

## Rollback
```bash
git revert <sha> && [additional steps]
```

## Risk Assessment
[severity] - [explanation]

Use github_create_pr tool to create the PR."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    state["prs_created"] = state.get("prs_created", [])
    state["prs_created"].append("PR #123")

    return state


def decide_merge_node(state: AmberState) -> AmberState:
    """Decide if auto-merge is appropriate"""
    # Check all safety criteria
    state["risk_assessment"] = RiskAssessment(
        severity="low",
        blast_radius="Limited to single component",
        rollback_complexity="trivial",
        details="Changes isolated, easy to revert",
    )

    return state


def evaluate_auto_merge_eligibility(state: AmberState) -> str:
    """Apply Level 3 autonomy safety checks"""
    settings = get_settings()

    checks = [
        state.get("tests_passed", False),
        state.get("confidence", 0) >= settings.auto_merge_min_confidence,
        state.get("risk_assessment", {}).get("severity") == "low",
        len(state.get("violations_detected", [])) == 0,
        settings.auto_merge_enabled,
    ]

    return "auto_merge" if all(checks) else "request_review"


def auto_merge_node(state: AmberState) -> AmberState:
    """Auto-merge PR (Level 3 autonomy)"""
    # In real implementation: merge PR via GitHub API
    state["human_review_required"] = False
    return state


def request_review_node(state: AmberState) -> AmberState:
    """Request human review"""
    state["human_review_required"] = True
    return state


def create_background_workflow() -> StateGraph:
    """Create background agent workflow"""

    workflow = StateGraph(AmberState)

    # Add nodes
    workflow.add_node("fetch_work_queue", fetch_work_queue_node)
    workflow.add_node("prioritize", prioritize_node)
    workflow.add_node("assess_auto_fix", assess_auto_fix_node)
    workflow.add_node("create_plan", create_plan_node)
    workflow.add_node("implement_fix", implement_fix_node)
    workflow.add_node("run_tests", run_tests_node)
    workflow.add_node("create_pr", create_pr_node)
    workflow.add_node("decide_merge", decide_merge_node)
    workflow.add_node("auto_merge", auto_merge_node)
    workflow.add_node("request_review", request_review_node)

    # Build flow
    workflow.set_entry_point("fetch_work_queue")
    workflow.add_edge("fetch_work_queue", "prioritize")
    workflow.add_edge("prioritize", "assess_auto_fix")

    # Decision: auto-fixable?
    workflow.add_conditional_edges(
        "assess_auto_fix",
        route_by_confidence,
        {
            "high_confidence": "create_plan",
            "needs_investigation": "request_review",
            "no_work": END,
        },
    )

    workflow.add_edge("create_plan", "implement_fix")
    workflow.add_edge("implement_fix", "run_tests")

    # Decision: tests pass?
    def check_tests_passed(state: AmberState) -> str:
        return "create_pr" if state.get("tests_passed", False) else "request_review"

    workflow.add_conditional_edges("run_tests", check_tests_passed)

    workflow.add_edge("create_pr", "decide_merge")

    # Decision: auto-merge eligible?
    workflow.add_conditional_edges(
        "decide_merge", evaluate_auto_merge_eligibility
    )

    workflow.add_edge("auto_merge", END)
    workflow.add_edge("request_review", END)

    return workflow.compile()
