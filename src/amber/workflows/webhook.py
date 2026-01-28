"""Webhook-triggered reactive workflow"""

from langgraph.graph import END, StateGraph
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from amber.config import get_settings
from amber.models import AmberState
from amber.tools import ALL_TOOLS


WEBHOOK_SYSTEM_PROMPT = """You are Amber operating in WEBHOOK mode for reactive intelligence.

Your responsibility: Respond to GitHub events with high-value, non-duplicate insights.

Rules:
- ONLY comment if you add unique value (not duplicate of CI/linter)
- Keep comments concise (1-3 sentences + action items)
- Reference CI checks where applicable
- Format using markdown

Event types you handle:
- issues.opened: Triage and label
- pull_request.opened: Quick review for standards
- push.main: Changelog and impact check"""


def parse_event_node(state: AmberState) -> AmberState:
    """Parse GitHub webhook event"""
    trigger = state.get("trigger", {})
    event_type = trigger.get("event_type", "")
    payload = trigger.get("payload", {})

    state["trigger"]["parsed_event"] = {
        "type": event_type,
        "repo": payload.get("repository", {}).get("full_name", ""),
        "number": payload.get("issue", {}).get("number")
        or payload.get("pull_request", {}).get("number"),
        "title": payload.get("issue", {}).get("title")
        or payload.get("pull_request", {}).get("title"),
        "body": payload.get("issue", {}).get("body")
        or payload.get("pull_request", {}).get("body"),
        "author": payload.get("sender", {}).get("login"),
    }

    state["messages"] = [SystemMessage(content=WEBHOOK_SYSTEM_PROMPT)]

    return state


def triage_issue_node(state: AmberState) -> AmberState:
    """Triage new issue with labels and severity"""
    settings = get_settings()
    llm_with_tools = ChatAnthropic(
        model=settings.llm_model,
        temperature=0.0,
        max_tokens=2000,
    ).bind_tools(ALL_TOOLS)

    parsed = state["trigger"]["parsed_event"]

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content=f"""Triage this issue:

Title: {parsed['title']}
Body: {parsed['body']}

Classify:
1. Component: backend, frontend, operator, runner, docs
2. Severity: P0 (critical), P1 (high), P2 (medium), P3 (low)
3. Type: bug, feature, enhancement, question
4. Related issues: search for similar issues

Suggest appropriate labels and potential assignee based on component.
Check if this is auto-fixable for amber:auto-fix label."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    return state


def review_pr_node(state: AmberState) -> AmberState:
    """Quick PR review for standards compliance"""
    settings = get_settings()
    llm_with_tools = ChatAnthropic(
        model=settings.llm_model,
        temperature=0.0,
        max_tokens=4000,
    ).bind_tools(ALL_TOOLS)

    parsed = state["trigger"]["parsed_event"]

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content=f"""Perform quick PR review:

PR Title: {parsed['title']}
PR Description: {parsed['body']}

Check:
1. Constitution compliance (use constitution checking tools)
2. Commit message format (conventional commits)
3. PR description completeness (what, why, testing, risk)
4. Breaking changes detection
5. File patterns (excessive line count per commit)

IMPORTANT: Only comment if you find issues not covered by CI checks.
If CI is already flagging the same issues, skip commenting."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    # Check if we should comment
    content = response.content.lower() if hasattr(response, "content") else ""
    state["should_comment"] = "no issues found" not in content and "ci covers" not in content

    return state


def update_changelog_node(state: AmberState) -> AmberState:
    """Update changelog for push to main"""
    settings = get_settings()
    llm_with_tools = ChatAnthropic(
        model=settings.llm_model,
        temperature=0.0,
        max_tokens=2000,
    ).bind_tools(ALL_TOOLS)

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content="""Analyze recent push to main branch:

1. Get recent commits using git_log
2. Check for breaking changes
3. Identify components affected
4. Assess downstream impact

If breaking changes detected, notify maintainers.
Otherwise, just update metrics."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    return state


def post_comment_node(state: AmberState) -> AmberState:
    """Post comment to GitHub"""
    settings = get_settings()
    llm_with_tools = ChatAnthropic(
        model=settings.llm_model,
        temperature=0.0,
        max_tokens=1000,
    ).bind_tools(ALL_TOOLS)

    parsed = state["trigger"]["parsed_event"]
    event_type = state["trigger"]["event_type"]

    if event_type == "github.issues.opened":
        comment_template = """🤖 **Amber Triage**

[Classification and labels]

**Suggested Priority:** [P0-P3]
**Component:** [component]
**Related:** [link to similar issues if any]
"""
    else:  # PR review
        comment_template = """🤖 **Amber Analysis**

[Key findings - only if not duplicate of CI]

**Constitution Compliance:** [status]
**Recommended Action:** [what to do]

<details>
<summary>Full Analysis</summary>

[Detailed findings]
</details>
"""

    messages = state["messages"]
    messages.append(
        HumanMessage(
            content=f"""Generate comment using this template:

{comment_template}

Based on analysis, create concise, actionable comment.
Use github_create_issue_comment tool to post it."""
        )
    )

    response = llm_with_tools.invoke(messages)
    state["messages"].append(response)

    state["comments_posted"] = state.get("comments_posted", [])
    state["comments_posted"].append(f"Comment on {event_type} #{parsed['number']}")

    return state


def should_post_comment(state: AmberState) -> str:
    """Decide if we should post comment"""
    # For issues, always comment with triage
    if state["trigger"]["event_type"] == "github.issues.opened":
        return "post_comment"

    # For PRs, only if we have unique insights
    if state.get("should_comment", False):
        return "post_comment"

    return END


def create_webhook_workflow() -> StateGraph:
    """Create webhook-triggered reactive workflow"""

    workflow = StateGraph(AmberState)

    # Add nodes
    workflow.add_node("parse_event", parse_event_node)
    workflow.add_node("triage_issue", triage_issue_node)
    workflow.add_node("review_pr", review_pr_node)
    workflow.add_node("update_changelog", update_changelog_node)
    workflow.add_node("post_comment", post_comment_node)

    # Build flow
    workflow.set_entry_point("parse_event")

    # Route by event type
    def route_by_event(state: AmberState) -> str:
        event_type = state["trigger"]["event_type"]
        if "issues.opened" in event_type:
            return "triage_issue"
        elif "pull_request.opened" in event_type:
            return "review_pr"
        elif "push" in event_type and "main" in event_type:
            return "update_changelog"
        else:
            return END

    workflow.add_conditional_edges("parse_event", route_by_event)

    # Issue triage always posts comment
    workflow.add_edge("triage_issue", "post_comment")

    # PR review conditionally posts
    workflow.add_conditional_edges("review_pr", should_post_comment)

    # Push to main just logs, no comment
    workflow.add_edge("update_changelog", END)

    workflow.add_edge("post_comment", END)

    return workflow.compile()
