"""Artifacts API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.storage_models import (
    Artifact,
    ArtifactCreate,
    ArtifactQuery
)

router = APIRouter(prefix="/storage/artifacts", tags=["artifacts"])


@router.post("", response_model=Artifact)
async def create_artifact(artifact: ArtifactCreate, request: Request):
    """Create artifact record."""
    backend = request.app.state.backend
    return await backend.create_artifact(artifact)


@router.get("/{artifact_id}", response_model=Artifact)
async def get_artifact(artifact_id: str, request: Request):
    """Get artifact by ID."""
    backend = request.app.state.backend
    artifact = await backend.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")
    
    return artifact


@router.get("", response_model=List[Artifact])
async def list_artifacts(
    request: Request,
    session_id: str,
    type: str = None,
    limit: int = 100,
    offset: int = 0
):
    """List artifacts."""
    backend = request.app.state.backend
    
    query = ArtifactQuery(
        session_id=session_id,
        type=type,
        limit=limit,
        offset=offset
    )
    
    return await backend.list_artifacts(query)


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str, request: Request):
    """Delete artifact."""
    backend = request.app.state.backend
    deleted = await backend.delete_artifact(artifact_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")
    
    return {"status": "deleted", "artifact_id": artifact_id}
