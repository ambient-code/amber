"""Supervisor graph for routing to appropriate workflow"""

from typing import Any

from langgraph.graph import END, StateGraph
from langchain_anthropic import ChatAnthropic

from amber.config import get_settings
from amber.models import AmberState, OperatingMode
from amber.workflows.on_demand import create_on_demand_workflow
from amber.workflows.background import create_background_workflow
from amber.workflows.scheduled import create_scheduled_workflow
from amber.workflows.webhook import create_webhook_workflow


def classify_mode_node(state: AmberState) -> AmberState:
    """Classify request mode if not already set"""
    if state.get("mode"):
        return state

    trigger = state.get("trigger", {})

    # Determine mode from trigger
    if trigger.get("event_type", "").startswith("github."):
        state["mode"] = "webhook"
    elif trigger.get("schedule_type"):
        state["mode"] = "scheduled"
    elif trigger.get("autonomous", False):
        state["mode"] = "background"
    else:
        state["mode"] = "on-demand"

    return state


def finalize_node(state: AmberState) -> AmberState:
    """Finalize workflow execution and prepare results"""
    state["current_phase"] = "completed"

    # Calculate final metrics - count total tokens from usage metadata if available
    total_tokens = 0
    for msg in state.get("messages", []):
        if hasattr(msg, "usage_metadata") and msg.usage_metadata:
            total_tokens += msg.usage_metadata.get("total_tokens", 0)
    state["token_count"] = total_tokens

    # Ensure all required fields are present
    if "findings" not in state:
        state["findings"] = []
    if "recommendations" not in state:
        state["recommendations"] = []
    if "prs_created" not in state:
        state["prs_created"] = []
    if "comments_posted" not in state:
        state["comments_posted"] = []

    return state


def route_to_workflow(state: AmberState) -> str:
    """Route to appropriate workflow based on mode"""
    return state["mode"]


def create_supervisor_graph() -> StateGraph:
    """Create supervisor graph that routes to appropriate workflow"""

    # Create individual workflow subgraphs
    on_demand_workflow = create_on_demand_workflow()
    background_workflow = create_background_workflow()
    scheduled_workflow = create_scheduled_workflow()
    webhook_workflow = create_webhook_workflow()

    # Build supervisor graph
    workflow = StateGraph(AmberState)

    # Add nodes
    workflow.add_node("classify_mode", classify_mode_node)
    workflow.add_node("on_demand", lambda state: on_demand_workflow.invoke(state))
    workflow.add_node("background", lambda state: background_workflow.invoke(state))
    workflow.add_node("scheduled", lambda state: scheduled_workflow.invoke(state))
    workflow.add_node("webhook", lambda state: webhook_workflow.invoke(state))
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("classify_mode")

    # Conditional routing to workflows
    workflow.add_conditional_edges(
        "classify_mode",
        route_to_workflow,
        {
            "on-demand": "on_demand",
            "background": "background",
            "scheduled": "scheduled",
            "webhook": "webhook",
        },
    )

    # All workflows converge to finalization
    workflow.add_edge("on_demand", "finalize")
    workflow.add_edge("background", "finalize")
    workflow.add_edge("scheduled", "finalize")
    workflow.add_edge("webhook", "finalize")
    workflow.add_edge("finalize", END)

    return workflow


def compile_supervisor_graph(checkpointer: Any = None) -> Any:
    """Compile supervisor graph with optional checkpointer"""
    workflow = create_supervisor_graph()
    return workflow.compile(checkpointer=checkpointer)
