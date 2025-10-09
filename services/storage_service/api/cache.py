"""Cache API routes."""

from fastapi import APIRouter, HTTPException, Request
from models.storage_models import (
    CacheEntry,
    CacheSet
)

router = APIRouter(prefix="/storage/cache", tags=["cache"])


@router.get("/{key}", response_model=CacheEntry)
async def cache_get(key: str, request: Request):
    """Get cached value."""
    backend = request.app.state.backend
    entry = await backend.cache_get(key)
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"Cache entry not found or expired: {key}")
    
    return entry


@router.put("/{key}", response_model=CacheEntry)
async def cache_set(key: str, cache: CacheSet, request: Request):
    """Set cache value."""
    backend = request.app.state.backend
    cache.key = key  # Use path parameter as key
    return await backend.cache_set(cache)


@router.delete("/{key}")
async def cache_delete(key: str, request: Request):
    """Delete cache entry."""
    backend = request.app.state.backend
    deleted = await backend.cache_delete(key)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Cache entry not found: {key}")
    
    return {"status": "deleted", "key": key}


@router.post("/cleanup")
async def cache_cleanup(request: Request):
    """Cleanup expired cache entries."""
    backend = request.app.state.backend
    deleted = await backend.cache_cleanup()
    
    return {"status": "completed", "deleted": deleted}
