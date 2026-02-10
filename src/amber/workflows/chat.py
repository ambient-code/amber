"""Interactive streaming chat workflow for Amber.

A simplified LangGraph workflow designed for multi-turn interactive chat
with checkpointing for conversation persistence. Unlike the on-demand
workflow which takes input from trigger.query, this workflow accepts
messages directly and maintains conversation history via the checkpointer.
"""

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import ToolNode

from amber.llm import get_llm
from amber.models import AmberState
from amber.tools import ALL_TOOLS

CHAT_SYSTEM_PROMPT = """You are Amber, the Ambient Code Platform's expert colleague and codebase intelligence agent.

Your core values:
1. High signal, low noise - Every response must add clear value
2. Anticipatory intelligence - Surface issues before they impact development
3. Execution over explanation - Show code, not concepts
4. Team fit - Respect project standards
5. User safety & trust - Explain actions, provide rollback instructions

You are in INTERACTIVE CHAT mode for real-time conversation with a developer.

Output format:
- Be concise but accurate
- Use file:line references when discussing code
- State your confidence level (High 90-100%, Medium 70-89%, Low <70%)
- Provide expandable details if needed

You have access to tools for:
- Code analysis (grep, read files, git history)
- Constitution compliance checking
- GitHub API operations

Always reference the ACP Constitution when making recommendations."""


def chat_agent_node(state: AmberState) -> dict:
    """Agent node that processes messages with tool binding."""
    llm = get_llm().bind_tools(ALL_TOOLS)

    messages = list(state.get("messages", []))

    # Prepend system prompt if this is the first interaction
    has_system = any(isinstance(m, SystemMessage) for m in messages)
    if not has_system:
        messages = [SystemMessage(content=CHAT_SYSTEM_PROMPT)] + messages

    response = llm.invoke(messages)

    return {"messages": [response]}


def should_continue(state: AmberState) -> str:
    """Route to tools if the last message has tool calls, otherwise end."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


def create_chat_workflow(checkpointer=None) -> CompiledGraph:
    """Create and compile the interactive chat workflow.

    Args:
        checkpointer: LangGraph checkpointer for conversation persistence.
            Required for multi-turn conversations.

    Returns:
        Compiled LangGraph workflow ready for streaming.
    """
    tool_node = ToolNode(ALL_TOOLS)

    workflow = StateGraph(AmberState)

    workflow.add_node("agent", chat_agent_node)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )

    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer)
