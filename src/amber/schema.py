"""Schema definitions for Amber chat streaming API.

Pydantic models and TypedDict definitions for request/response validation
and data serialization for the streaming chat endpoints.
"""

from typing import Any, Literal, NotRequired, TypedDict

from pydantic import BaseModel, Field


class StreamRequest(BaseModel):
    """Request model for streaming chat responses."""

    message: str = Field(
        description="User input message to be processed by the agent.",
        examples=["What is the status of our CI pipeline?"],
    )
    thread_id: str | None = Field(
        description="Thread ID to persist and continue a multi-turn conversation. Auto-generated if not provided.",
        default=None,
    )
    session_id: str | None = Field(
        description="Session ID to persist and continue a conversation across multiple threads.",
        default=None,
    )
    user_id: str | None = Field(
        description="User ID to persist and continue a conversation across multiple threads.",
        default=None,
    )
    stream_tokens: bool = Field(
        description="Whether to stream LLM tokens to the client in real-time.",
        default=True,
    )


class ToolCall(TypedDict):
    """Represents a request to call a tool."""

    name: str
    args: dict[str, Any]
    id: str | None
    type: NotRequired[Literal["tool_call"]]


class ChatMessage(BaseModel):
    """Message model for chat conversations."""

    type: Literal["human", "ai", "tool", "custom"] = Field(
        description="The role or type of the message in the conversation.",
    )
    content: str = Field(
        description="The text content of the message.",
    )
    tool_calls: list[ToolCall] = Field(
        description="Tool calls included in this message.",
        default=[],
    )
    tool_call_id: str | None = Field(
        description="ID of the tool call that this message is responding to.",
        default=None,
    )
    run_id: str | None = Field(
        description="Run ID associated with this message for tracking.",
        default=None,
    )
    thread_id: str | None = Field(
        description="Thread ID associated with this message for conversation tracking.",
        default=None,
    )
    session_id: str | None = Field(
        description="Session ID associated with this message for session tracking.",
        default=None,
    )
    response_metadata: dict[str, Any] = Field(
        description="Additional metadata for the response.",
        default={},
    )


class ChatHistoryResponse(BaseModel):
    """Response model for chat history requests."""

    messages: list[ChatMessage]
