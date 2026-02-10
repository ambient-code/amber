"""Utility functions for handling agent messages and conversions.

Provides functions for converting between LangChain message formats
and the Amber ChatMessage schema, handling content normalization,
and filtering tool calls from streaming content.
"""

from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)

from amber.schema import ChatMessage, ToolCall


def convert_message_content_to_string(
    content: str | list[str | dict[str, Any]],
) -> str:
    """Convert message content to string format.

    Handles str and list content (as returned by Anthropic models),
    extracting text items and concatenating them.
    """
    if isinstance(content, str):
        return content

    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])

    return "".join(text)


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    """Convert a LangChain message to a ChatMessage.

    Handles HumanMessage, AIMessage, and ToolMessage types,
    preserving tool calls and response metadata.
    """
    match message:
        case HumanMessage():
            return ChatMessage(
                type="human",
                content=convert_message_content_to_string(message.content),
            )

        case AIMessage():
            ai_message = ChatMessage(
                type="ai",
                content=convert_message_content_to_string(message.content),
            )
            tool_calls = message.tool_calls or []
            if message.additional_kwargs and "tool_calls" in message.additional_kwargs:
                tool_calls.extend(message.additional_kwargs["tool_calls"])

            if tool_calls:
                formatted_tool_calls = []
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        if "name" in tool_call and "args" in tool_call:
                            formatted_call: ToolCall = {
                                "name": str(tool_call["name"]),
                                "args": dict(tool_call["args"]),
                                "id": str(tool_call.get("id")) if tool_call.get("id") else None,
                                "type": "tool_call",
                            }
                            formatted_tool_calls.append(formatted_call)
                ai_message.tool_calls = formatted_tool_calls

            if message.response_metadata:
                ai_message.response_metadata = message.response_metadata

            return ai_message

        case ToolMessage():
            return ChatMessage(
                type="tool",
                content=convert_message_content_to_string(message.content),
                tool_call_id=message.tool_call_id,
            )

        case _:
            raise ValueError(f"Unsupported message type: {message.__class__.__name__}")


def remove_tool_calls(
    content: str | list[str | dict[str, Any]],
) -> str | list[str | dict[str, Any]]:
    """Remove tool_use content items from message content.

    Filters out tool_use blocks that Anthropic models include
    in streaming content alongside text.
    """
    if isinstance(content, str):
        return content

    return [content_item for content_item in content if isinstance(content_item, str) or content_item["type"] != "tool_use"]
