"""On-demand consultation workflow"""

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from amber.llm import get_llm
from amber.models import AmberState
from amber.tools import ALL_TOOLS


AMBER_SYSTEM_PROMPT = """You are Amber, the Ambient Code Platform's expert colleague and codebase intelligence agent.

Your core values:
1. High signal, low noise - Every response must add clear value
2. Anticipatory intelligence - Surface issues before they impact development
3. Execution over explanation - Show code, not concepts
4. Team fit - Respect project standards
5. User safety & trust - Explain actions, provide rollback instructions

Operating in ON-DEMAND mode for interactive consultation.

Output format:
- 2-sentence summary with file:line references
- State your confidence level (High 90-100%, Medium 70-89%, Low <70%)
- Expandable details if needed
- Be concise but accurate

You have access to tools for:
- Code analysis (grep, read files, git history)
- Constitution compliance checking
- GitHub API operations

Always reference the ACP Constitution when making recommendations."""


def agent_node(state: AmberState) -> AmberState:
    """Main agent node that processes messages and decides on actions"""
    # Create LLM with tools
    llm = get_llm(max_tokens=4000).bind_tools(ALL_TOOLS)

    messages = state.get("messages", [])

    # Initialize messages if empty
    if not messages:
        trigger = state.get("trigger", {})
        user_query = trigger.get("query", "")
        messages = [
            SystemMessage(content=AMBER_SYSTEM_PROMPT),
            HumanMessage(content=user_query),
        ]

    # Invoke LLM
    response = llm.invoke(messages)

    # Update state
    state["messages"] = messages + [response]
    state["current_phase"] = "analyzing"

    return state


def should_continue(state: AmberState) -> str:
    """Determine if we should continue to tools or end"""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]

    # Check if last message has tool calls
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


def create_on_demand_workflow() -> StateGraph:
    """Create on-demand consultation workflow"""

    # Create tool node
    tool_node = ToolNode(ALL_TOOLS)

    # Build workflow
    workflow = StateGraph(AmberState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )

    # Tools always return to agent
    workflow.add_edge("tools", "agent")

    return workflow.compile()
