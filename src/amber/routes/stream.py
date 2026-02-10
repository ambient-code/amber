"""Streaming chat endpoint for Amber.

POST /v1/stream - Accepts a StreamRequest, streams LangGraph events
as Server-Sent Events (SSE) to the client.
"""

import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig

from amber.schema import StreamRequest
from amber.utils.message_utils import (
    convert_message_content_to_string,
    langchain_to_chat_message,
    remove_tool_calls,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level reference to the chat graph, set by service.py lifespan
chat_graph = None


@router.post("/v1/stream")
async def stream_chat(
    request: StreamRequest,
    x_token: str | None = Header(None, alias="X-Token"),
):
    """Stream agent response as SSE events.

    Accepts a user message, runs it through the Amber chat workflow,
    and streams back message updates and token-by-token content.

    Each SSE frame is: json.dumps(event) + "\\n\\n"
    Stream ends with [DONE]\\n\\n
    """
    if chat_graph is None:
        raise HTTPException(status_code=503, detail="Chat graph not initialized")

    thread_id = request.thread_id or str(uuid4())
    run_id = str(uuid4())
    effective_session_id = request.session_id or thread_id
    effective_user_id = request.user_id or "anonymous"

    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "user_id": effective_user_id,
            "session_id": effective_session_id,
            "run_id": run_id,
        },
        run_id=run_id,
    )

    input_message = {"messages": [HumanMessage(content=request.message)]}

    async def event_generator():
        try:
            async for stream_event in chat_graph.astream(
                input_message,
                config=config,
                stream_mode=["updates", "messages"],
            ):
                if not isinstance(stream_event, tuple):
                    continue

                stream_mode, event = stream_event

                if stream_mode == "updates":
                    for node, node_updates in event.items():
                        if node == "__interrupt__":
                            continue
                        update_messages = (node_updates or {}).get("messages", [])
                        for message in update_messages:
                            try:
                                chat_message = langchain_to_chat_message(message)
                                chat_message.run_id = run_id
                                content = {
                                    "type": chat_message.type,
                                    "content": chat_message.content,
                                    "run_id": run_id,
                                    "thread_id": thread_id,
                                    "session_id": effective_session_id,
                                }
                                if chat_message.tool_calls:
                                    content["tool_calls"] = chat_message.tool_calls
                                if chat_message.tool_call_id:
                                    content["tool_call_id"] = chat_message.tool_call_id
                                if chat_message.response_metadata:
                                    content["response_metadata"] = chat_message.response_metadata

                                formatted_event = {"type": "message", "content": content}
                                yield json.dumps(formatted_event) + "\n\n"
                            except Exception as e:
                                logger.error(f"Error formatting update message: {e}")
                                continue

                elif stream_mode == "messages" and request.stream_tokens:
                    msg, metadata = event
                    if "skip_stream" in metadata.get("tags", []):
                        continue
                    if not isinstance(msg, AIMessageChunk):
                        continue

                    content = remove_tool_calls(msg.content)
                    if content:
                        text = convert_message_content_to_string(content)
                        if text:
                            token_event = {"type": "token", "content": text}
                            yield json.dumps(token_event) + "\n\n"

        except Exception as e:
            logger.error(f"Error in stream: {e}")
            error_event = {
                "type": "error",
                "content": {"message": "Internal server error", "recoverable": False},
            }
            yield json.dumps(error_event) + "\n\n"

        yield "[DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id,
        },
    )
