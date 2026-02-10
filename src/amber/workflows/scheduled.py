"""Scheduled workflow for periodic health checks"""

from datetime import datetime
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage

from amber.llm import get_llm
from amber.models import AmberState
from amber.tools import ALL_TOOLS


SCHEDULED_SYSTEM_PROMPT = """You are Amber operating in SCHEDULED mode for periodic health checks.

Your responsibility: Proactive monitoring and reporting on codebase health.

Report types:
- NIGHTLY: Dependency scans, security alerts, CI status
- WEEKLY: Sprint planning, issue clustering, test coverage
- MONTHLY: Architecture review, tech debt assessment

Output: Markdown report following GitLab standards, committed to feature branch."""


def determine_report_type_node(state: AmberState) -> AmberState:
    """Determine report type from trigger"""
    trigger = state.get("trigger", {})
    schedule_type = trigger.get("schedule_type", "nightly")

    state["trigger"]["schedule_type"] = schedule_type
    state["messages"] = [SystemMessage(content=SCHEDULED_SYSTEM_PROMPT)]

    return state


def scan_dependencies_node(state: AmberState) -> AmberState:
    """Scan upstream dependencies for breaking changes"""
    llm_with_tools = get_llm(max_tokens=4000).bind_tools(ALL_TOOLS)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Perform nightly dependency scan:

1. Check for security vulnerabilities in dependencies
2. Look for upstream breaking changes in:
   - kubernetes/kubernetes
   - anthropics/anthropic-sdk-python
   - openshift libraries
   - langfuse
3. Check if dependencies are up-to-date
4. Identify deprecated APIs being used

Use grep_codebase and read_file tools to analyze go.mod, package.json, requirements.txt"""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    return state


def check_security_node(state: AmberState) -> AmberState:
    """Check for security issues"""
    llm_with_tools = get_llm(max_tokens=4000).bind_tools(ALL_TOOLS)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Perform security audit:

1. Check for constitution Principle II violations:
   - Token/secret logging
   - Missing RBAC checks
   - Improper service account usage
2. Search for common security anti-patterns
3. Review authentication and authorization code
4. Check for exposed sensitive endpoints

Use constitution checking tools and code analysis."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    return state


def analyze_issues_node(state: AmberState) -> AmberState:
    """Analyze issue backlog for sprint planning"""
    llm_with_tools = get_llm(max_tokens=4000).bind_tools(ALL_TOOLS)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Perform weekly issue analysis:

1. Fetch all open issues using github_list_issues
2. Cluster issues by theme:
   - Same component affected
   - Same root cause
   - Related features
3. Identify high-priority issues without assignees
4. Detect stale issues (no activity in >30 days)
5. Recommend sprint focus areas

Generate insights for sprint planning."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    return state


def generate_report_node(state: AmberState) -> AmberState:
    """Generate markdown report"""
    llm = get_llm(max_tokens=4000)

    schedule_type = state["trigger"]["schedule_type"]
    report_date = datetime.now().strftime("%Y-%m-%d")

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content=f"""Generate {schedule_type.upper()} report using GitLab formatting standards:

# {schedule_type.capitalize()} Health Check - {report_date}

## Executive Summary
[2-3 sentences: key findings, recommended actions]

## Findings
[Bulleted list with severity tags: Critical/High/Medium/Low]

## Recommended Actions
1. [Action] - Priority: [P0-P3], Effort: [Low/Med/High], Owner: [suggest]

## Metrics
[Relevant metrics based on report type]

## Next Review
[When to re-assess, what to monitor]

Be concise but comprehensive. Use markdown formatting."""
        )
    )

    response = llm.invoke(messages)
    state["messages"].append(response)

    # Store report content
    state["plan"] = {
        "report_type": schedule_type,
        "report_date": report_date,
        "content": response.content if hasattr(response, "content") else "",
    }

    return state


def commit_report_node(state: AmberState) -> AmberState:
    """Commit report to repository"""
    # In real implementation:
    # 1. Create feature branch
    # 2. Write report to docs/amber-reports/
    # 3. Commit with conventional commit message
    # 4. Push branch

    schedule_type = state["trigger"]["schedule_type"]
    report_date = state["plan"]["report_date"]
    branch_name = f"amber/{schedule_type}-report-{report_date}"

    state["branches_created"] = state.get("branches_created", [])
    state["branches_created"].append(branch_name)

    return state


def create_report_pr_node(state: AmberState) -> AmberState:
    """Create PR with report"""
    llm_with_tools = get_llm(max_tokens=2000).bind_tools(ALL_TOOLS)

    schedule_type = state["trigger"]["schedule_type"]
    report_date = state["plan"]["report_date"]

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content=f"""Create PR for {schedule_type} report:

Title: {schedule_type.capitalize()} Health Check - {report_date}

Body:
Automated {schedule_type} health check report by Amber.

## Summary
[Extract key findings from report]

## Action Required
[Highlight P0/P1 items if any]

🤖 Generated by Amber

Use github_create_pr tool."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    state["prs_created"] = state.get("prs_created", [])
    state["prs_created"].append(f"PR: {schedule_type} report {report_date}")

    return state


def create_scheduled_workflow() -> StateGraph:
    """Create scheduled health check workflow"""

    workflow = StateGraph(AmberState)

    # Add nodes
    workflow.add_node("determine_report_type", determine_report_type_node)
    workflow.add_node("scan_dependencies", scan_dependencies_node)
    workflow.add_node("check_security", check_security_node)
    workflow.add_node("analyze_issues", analyze_issues_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("commit_report", commit_report_node)
    workflow.add_node("create_report_pr", create_report_pr_node)

    # Build flow
    workflow.set_entry_point("determine_report_type")

    # Route by schedule type
    def route_by_schedule(state: AmberState) -> str:
        return state["trigger"]["schedule_type"]

    workflow.add_conditional_edges(
        "determine_report_type",
        route_by_schedule,
        {
            "nightly": "scan_dependencies",
            "weekly": "analyze_issues",
            "monthly": "check_security",
        },
    )

    # All converge to report generation
    workflow.add_edge("scan_dependencies", "generate_report")
    workflow.add_edge("analyze_issues", "generate_report")
    workflow.add_edge("check_security", "generate_report")
    workflow.add_edge("generate_report", "commit_report")
    workflow.add_edge("commit_report", "create_report_pr")
    workflow.add_edge("create_report_pr", END)

    return workflow.compile()
