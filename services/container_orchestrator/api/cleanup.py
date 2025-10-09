"""Cleanup API routes."""

from fastapi import APIRouter, Request
from models.container_models import (
    SessionCleanupRequest,
    SessionCleanupResult
)

router = APIRouter(prefix="/containers/cleanup", tags=["cleanup"])


@router.post("/session", response_model=SessionCleanupResult)
async def cleanup_session(request_data: SessionCleanupRequest, req: Request):
    """Cleanup all containers for a session."""
    docker_manager = req.app.state.docker_manager
    network_manager = req.app.state.network_manager
    
    # Cleanup containers
    result = await docker_manager.cleanup_session(request_data.session_id, request_data.force)
    
    # Cleanup network
    network_removed = network_manager.remove_session_network(request_data.session_id)
    
    return SessionCleanupResult(
        session_id=request_data.session_id,
        containers_removed=result["containers_removed"],
        networks_removed=1 if network_removed else 0,
        volumes_removed=0,  # Not tracking volumes separately yet
        errors=result["errors"]
    )


@router.post("/all-networks")
async def cleanup_all_networks(req: Request):
    """Cleanup all managed session networks."""
    network_manager = req.app.state.network_manager
    
    removed = network_manager.cleanup_all_session_networks()
    
    return {"status": "completed", "networks_removed": removed}
