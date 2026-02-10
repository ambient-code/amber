"""Amber workflow implementations"""

from amber.workflows.background import create_background_workflow
from amber.workflows.chat import create_chat_workflow
from amber.workflows.on_demand import create_on_demand_workflow
from amber.workflows.scheduled import create_scheduled_workflow
from amber.workflows.supervisor import compile_supervisor_graph, create_supervisor_graph
from amber.workflows.webhook import create_webhook_workflow

__all__ = [
    "compile_supervisor_graph",
    "create_supervisor_graph",
    "create_on_demand_workflow",
    "create_background_workflow",
    "create_scheduled_workflow",
    "create_webhook_workflow",
    "create_chat_workflow",
]
