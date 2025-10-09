"""Tool execution API routes."""

from fastapi import APIRouter, HTTPException, Request
from models.container_models import (
    ToolExecutionRequest,
    ToolExecutionResult
)

router = APIRouter(prefix="/containers/tool", tags=["tools"])


@router.post("/execute", response_model=ToolExecutionResult)
async def execute_tool(request_data: ToolExecutionRequest, req: Request):
    """Execute a tool in an ephemeral container."""
    docker_manager = req.app.state.docker_manager
    
    # Execute tool
    result = await docker_manager.execute_tool(request_data)
    
    return result


@router.get("/{execution_id}", response_model=ToolExecutionResult)
async def get_execution(execution_id: str, req: Request):
    """Get execution result by ID."""
    docker_manager = req.app.state.docker_manager
    
    result = docker_manager.get_execution(execution_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    
    return result


@router.get("/{execution_id}/logs")
async def get_execution_logs(execution_id: str, req: Request):
    """Get execution logs."""
    docker_manager = req.app.state.docker_manager
    
    try:
        logs = docker_manager.get_execution_logs(execution_id)
        return logs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{execution_id}/cancel")
async def cancel_execution(execution_id: str, req: Request):
    """Cancel a running execution."""
    docker_manager = req.app.state.docker_manager
    
    success = await docker_manager.cancel_execution(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Could not cancel execution: {execution_id} (not found or not running)"
        )
    
    return {"status": "cancelled", "execution_id": execution_id}
