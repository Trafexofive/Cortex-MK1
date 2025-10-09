"""Metrics API routes."""

from fastapi import APIRouter, Request
from typing import List, Optional
from datetime import datetime
from models.storage_models import (
    Metric,
    MetricCreate,
    MetricQuery
)

router = APIRouter(prefix="/storage/metrics", tags=["metrics"])


@router.post("", response_model=Metric)
async def record_metric(metric: MetricCreate, request: Request):
    """Record a metric."""
    backend = request.app.state.backend
    return await backend.record_metric(metric)


@router.get("", response_model=List[Metric])
async def query_metrics(
    request: Request,
    entity_type: Optional[str] = None,
    entity_name: Optional[str] = None,
    session_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Query metrics."""
    backend = request.app.state.backend
    
    query = MetricQuery(
        entity_type=entity_type,
        entity_name=entity_name,
        session_id=session_id,
        metric_name=metric_name,
        start_time=datetime.fromisoformat(start_time) if start_time else None,
        end_time=datetime.fromisoformat(end_time) if end_time else None,
        limit=limit,
        offset=offset
    )
    
    return await backend.query_metrics(query)
