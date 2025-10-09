"""Message/history API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.storage_models import (
    Message,
    MessageCreate,
    MessageQuery
)

router = APIRouter(prefix="/storage/history", tags=["history"])


@router.post("", response_model=Message)
async def add_message(message: MessageCreate, request: Request):
    """Add message to conversation history."""
    backend = request.app.state.backend
    return await backend.add_message(message)


@router.get("", response_model=List[Message])
async def get_messages(
    request: Request,
    session_id: str,
    role: str = None,
    limit: int = 100,
    offset: int = 0
):
    """Get conversation history."""
    backend = request.app.state.backend
    
    query = MessageQuery(
        session_id=session_id,
        role=role,
        limit=limit,
        offset=offset
    )
    
    return await backend.get_messages(query)


@router.delete("")
async def delete_messages(session_id: str, request: Request):
    """Delete all messages for a session."""
    backend = request.app.state.backend
    deleted = await backend.delete_messages(session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No messages found for session: {session_id}")
    
    return {"status": "deleted", "session_id": session_id}
