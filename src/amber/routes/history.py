"""Chat history endpoint for Amber.

GET /v1/history/{thread_id} - Retrieves conversation history
using the LangGraph checkpointer for proper message deserialization.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from langgraph.checkpoint.base import BaseCheckpointSaver

from amber.schema import ChatHistoryResponse, ChatMessage
from amber.utils.message_utils import langchain_to_chat_message

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level reference to the checkpointer, set by service.py lifespan
checkpointer: BaseCheckpointSaver | None = None


def _get_history(thread_id: str) -> list[ChatMessage]:
    """Fetch and convert checkpoint messages for a thread (blocking)."""
    if checkpointer is None:
        return []

    config = {"configurable": {"thread_id": thread_id}}
    checkpoint_tuple = checkpointer.get_tuple(config)

    if not checkpoint_tuple:
        logger.info(f"No checkpoints found for thread_id: {thread_id}")
        return []

    channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
    messages = channel_values.get("messages", [])
    logger.info(f"Found {len(messages)} messages in checkpoint for thread_id: {thread_id}")

    metadata = checkpoint_tuple.metadata or {}
    run_id = metadata.get("run_id")
    session_id = metadata.get("session_id")

    chat_messages: list[ChatMessage] = []
    for message in messages:
        try:
            chat_message = langchain_to_chat_message(message)
            if run_id:
                chat_message.run_id = run_id
            chat_message.thread_id = thread_id
            if session_id:
                chat_message.session_id = session_id
            chat_messages.append(chat_message)
        except Exception as e:
            logger.warning(f"Could not convert checkpoint message: {e}")
            continue

    return chat_messages


@router.get("/v1/history/{thread_id}")
async def history(thread_id: str) -> ChatHistoryResponse:
    """Get chat history for a specific thread.

    Uses the LangGraph checkpointer to retrieve and deserialize
    the checkpoint state, ensuring messages are proper LangChain
    objects for conversion.
    """
    try:
        chat_messages = await asyncio.to_thread(_get_history, thread_id)
        logger.info(f"Retrieved {len(chat_messages)} messages for thread_id: {thread_id}")
        return ChatHistoryResponse(messages=chat_messages)
    except Exception as e:
        logger.error(f"Error fetching history for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")
