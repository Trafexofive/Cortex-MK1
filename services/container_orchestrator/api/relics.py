"""Relic management API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from models.container_models import (
    RelicStartRequest,
    RelicInfo
)

router = APIRouter(prefix="/containers/relic", tags=["relics"])


@router.post("/start", response_model=RelicInfo)
async def start_relic(request_data: RelicStartRequest, req: Request):
    """Start a relic container."""
    docker_manager = req.app.state.docker_manager
    network_manager = req.app.state.network_manager
    
    # Create private network for session if requested
    network_id = None
    if request_data.create_private_network:
        network_id = network_manager.create_session_network(request_data.session_id)
    
    # Start relic
    try:
        relic_info = await docker_manager.start_relic(request_data, network_id)
        return relic_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start relic: {str(e)}")


@router.get("/{relic_id}", response_model=RelicInfo)
async def get_relic(relic_id: str, req: Request):
    """Get relic info by ID."""
    docker_manager = req.app.state.docker_manager
    
    relic = docker_manager.get_relic(relic_id)
    if not relic:
        raise HTTPException(status_code=404, detail=f"Relic not found: {relic_id}")
    
    return relic


@router.get("", response_model=List[RelicInfo])
async def list_relics(session_id: Optional[str] = None, req: Request = None):
    """List relics, optionally filtered by session."""
    docker_manager = req.app.state.docker_manager
    
    relics = docker_manager.list_relics(session_id)
    return relics


@router.post("/{relic_id}/stop")
async def stop_relic(relic_id: str, req: Request):
    """Stop a relic container."""
    docker_manager = req.app.state.docker_manager
    
    success = await docker_manager.stop_relic(relic_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Relic not found: {relic_id}")
    
    return {"status": "stopped", "relic_id": relic_id}


@router.delete("/{relic_id}")
async def delete_relic(relic_id: str, req: Request):
    """Delete a relic container (alias for stop)."""
    docker_manager = req.app.state.docker_manager
    
    success = await docker_manager.stop_relic(relic_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Relic not found: {relic_id}")
    
    return {"status": "deleted", "relic_id": relic_id}
