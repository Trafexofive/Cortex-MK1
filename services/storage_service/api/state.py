"""Agent state API routes."""

from fastapi import APIRouter, HTTPException, Request
from models.storage_models import (
    AgentState,
    StateUpdate
)

router = APIRouter(prefix="/storage/state", tags=["state"])


@router.get("/{session_id}", response_model=AgentState)
async def get_state(session_id: str, request: Request):
    """Get agent state."""
    backend = request.app.state.backend
    state = await backend.get_state(session_id)
    
    if not state:
        # Return empty state if not found
        return AgentState(session_id=session_id, data={})
    
    return state


@router.put("/{session_id}", response_model=AgentState)
async def set_state(session_id: str, update: StateUpdate, request: Request):
    """Set agent state."""
    backend = request.app.state.backend
    return await backend.set_state(session_id, update)


@router.delete("/{session_id}")
async def delete_state(session_id: str, request: Request):
    """Delete agent state."""
    backend = request.app.state.backend
    deleted = await backend.delete_state(session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"State not found for session: {session_id}")
    
    return {"status": "deleted", "session_id": session_id}
