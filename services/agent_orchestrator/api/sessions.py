"""Session management API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.orchestrator_models import (
    SessionCreateRequest,
    SessionInfo
)

router = APIRouter(prefix="/agent", tags=["sessions"])


@router.post("/{agent_name}/session", response_model=SessionInfo)
async def create_session(agent_name: str, request_data: SessionCreateRequest, req: Request):
    """Create a new agent session."""
    session_manager = req.app.state.session_manager
    
    # Override agent_name from path
    request_data.agent_name = agent_name
    
    try:
        session_info = await session_manager.create_session(request_data)
        return session_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, req: Request):
    """Get session info."""
    session_manager = req.app.state.session_manager
    
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return session_info


@router.delete("/session/{session_id}")
async def end_session(session_id: str, req: Request):
    """End a session and cleanup resources."""
    session_manager = req.app.state.session_manager
    
    success = await session_manager.end_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return {"status": "ended", "session_id": session_id}


@router.get("/session/{session_id}/history")
async def get_history(session_id: str, req: Request, limit: int = 50):
    """Get conversation history."""
    session_manager = req.app.state.session_manager
    
    # Load from storage directly
    history = await session_manager._load_history(session_id)
    return {"session_id": session_id, "messages": history[-limit:]}


@router.get("/session/{session_id}/state")
async def get_state(session_id: str, req: Request):
    """Get agent state."""
    session_manager = req.app.state.session_manager
    
    state = await session_manager._load_state(session_id)
    return {"session_id": session_id, "state": state}
