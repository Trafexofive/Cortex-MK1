"""Session management API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.storage_models import (
    Session,
    SessionCreate,
    SessionUpdate,
    SessionQuery
)

router = APIRouter(prefix="/storage/sessions", tags=["sessions"])


@router.post("", response_model=Session)
async def create_session(session: SessionCreate, request: Request):
    """Create a new session."""
    backend = request.app.state.backend
    return await backend.create_session(session)


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str, request: Request):
    """Get session by ID."""
    backend = request.app.state.backend
    session = await backend.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return session


@router.put("/{session_id}", response_model=Session)
async def update_session(session_id: str, update: SessionUpdate, request: Request):
    """Update session."""
    backend = request.app.state.backend
    session = await backend.update_session(session_id, update)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, request: Request):
    """Delete session and all related data."""
    backend = request.app.state.backend
    deleted = await backend.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return {"status": "deleted", "session_id": session_id}


@router.get("", response_model=List[Session])
async def list_sessions(
    request: Request,
    agent_name: str = None,
    user_id: str = None,
    status: str = None,
    limit: int = 100,
    offset: int = 0
):
    """List sessions with filtering."""
    backend = request.app.state.backend
    
    query = SessionQuery(
        agent_name=agent_name,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return await backend.list_sessions(query)
