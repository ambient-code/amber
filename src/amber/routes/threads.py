"""Thread listing endpoint for Amber.

GET /v1/threads/{user_id} - Lists all thread IDs for a given user
by querying the PostgreSQL checkpoints table metadata.
"""

import asyncio
import logging

import psycopg2
from fastapi import APIRouter, HTTPException

from amber.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_threads(user_id: str) -> list[str]:
    """Query distinct thread IDs for a user (blocking)."""
    settings = get_settings()

    with psycopg2.connect(settings.postgres_url) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT thread_id FROM checkpoints WHERE metadata->>'user_id' = %s",
            (user_id,),
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]


@router.get("/v1/threads/{user_id}")
async def list_threads(user_id: str) -> list[str]:
    """Get all thread IDs for a specific user.

    Queries the checkpoints table for distinct thread_ids where
    the metadata user_id matches the given user_id.
    """
    try:
        thread_ids = await asyncio.to_thread(_get_threads, user_id)
        logger.info(f"Found {len(thread_ids)} threads for user_id: {user_id}")
        return thread_ids
    except Exception as e:
        logger.error(f"Error fetching threads for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threads")
