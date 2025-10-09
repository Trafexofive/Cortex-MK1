"""Container stats API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from models.container_models import ContainerStats

router = APIRouter(prefix="/containers/stats", tags=["stats"])


@router.get("", response_model=List[ContainerStats])
async def list_stats(req: Request):
    """Get stats for all containers."""
    docker_manager = req.app.state.docker_manager
    
    stats = docker_manager.list_all_stats()
    return stats


@router.get("/{container_id}", response_model=ContainerStats)
async def get_stats(container_id: str, req: Request):
    """Get stats for a specific container."""
    docker_manager = req.app.state.docker_manager
    
    stats = docker_manager.get_container_stats(container_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail=f"Container not found or no stats available: {container_id}")
    
    return stats
