"""
==============================================================================
RUNTIME EXECUTOR SERVICE v1.0
==============================================================================
FastAPI service for executing manifest-defined entities (Tools, Agents, etc.)
Provides secure, sandboxed execution of Python scripts, shell commands, and more.

Philosophy:
- Manifest-Driven: All execution is based on validated manifest definitions
- Sandboxed: Secure execution with resource limits and isolation
- Observable: Full logging and monitoring of execution
- Polymorphic: Support for multiple runtime types (Python, Shell, Docker, etc.)
==============================================================================
"""

import os
import asyncio
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger
import httpx

# Import runtime execution models
from models.execution_models import (
    ExecutionRequest,
    ExecutionResponse,
    RuntimeType,
    ExecutionStatus,
    ResourceLimits,
    ExecutionContext
)
from executors.python_executor import PythonExecutor
from executors.shell_executor import ShellExecutor  
from executors.docker_executor import DockerExecutor
from registry.execution_registry import ExecutionRegistry


# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    logger.info("🚀 Starting Runtime Executor Service...")
    
    # Initialize execution registry
    app.state.registry = ExecutionRegistry()
    
    # Initialize executors
    app.state.executors = {
        RuntimeType.PYTHON: PythonExecutor(),
        RuntimeType.SHELL: ShellExecutor(),
        RuntimeType.DOCKER: DockerExecutor()
    }
    
    # Connect to manifest ingestion service
    app.state.manifest_service_url = os.getenv("MANIFEST_INGESTION_URL", "http://manifest_ingestion:8082")
    
    logger.info("✅ Runtime Executor Service ready")
    yield
    
    logger.info("🛑 Shutting down Runtime Executor Service...")


# FastAPI App
app = FastAPI(
    title="Cortex-Prime Runtime Executor Service",
    description="Secure execution of manifest-defined entities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "runtime-executor", 
        "version": "1.0.0",
        "executors": list(app.state.executors.keys())
    }


@app.get("/executors")
async def list_executors():
    """List available runtime executors"""
    return {
        "executors": [
            {
                "type": runtime_type.value,
                "status": await executor.get_status(),
                "capabilities": await executor.get_capabilities()
            }
            for runtime_type, executor in app.state.executors.items()
        ]
    }


# ============================================================================
# EXECUTION ENDPOINTS
# ============================================================================

@app.post("/execute/tool")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    context: Optional[ExecutionContext] = None
):
    """
    Execute a tool by name with given parameters
    """
    try:
        # Fetch tool manifest from ingestion service
        tool_manifest = await _fetch_manifest("Tool", tool_name)
        if not tool_manifest:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Create execution request
        execution_request = ExecutionRequest(
            entity_type="tool",
            entity_name=tool_name,
            parameters=parameters,
            context=context or ExecutionContext(),
            manifest_data=tool_manifest
        )
        
        # Execute the tool
        result = await _execute_entity(execution_request)
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute tool {tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute/agent")
async def execute_agent(
    agent_name: str,
    input_data: Dict[str, Any],
    context: Optional[ExecutionContext] = None
):
    """
    Execute an agent by name with given input data
    """
    try:
        # Fetch agent manifest from ingestion service
        agent_manifest = await _fetch_manifest("Agent", agent_name)
        if not agent_manifest:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Create execution request
        execution_request = ExecutionRequest(
            entity_type="agent",
            entity_name=agent_name,
            parameters=input_data,
            context=context or ExecutionContext(),
            manifest_data=agent_manifest
        )
        
        # Execute the agent
        result = await _execute_entity(execution_request)
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute/workflow")
async def execute_workflow(
    workflow_name: str,
    input_data: Dict[str, Any],
    context: Optional[ExecutionContext] = None
):
    """
    Execute a workflow by name with given input data
    """
    try:
        # Fetch workflow manifest from ingestion service
        workflow_manifest = await _fetch_manifest("Workflow", workflow_name)
        if not workflow_manifest:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")
        
        # Create execution request
        execution_request = ExecutionRequest(
            entity_type="workflow",
            entity_name=workflow_name,
            parameters=input_data,
            context=context or ExecutionContext(),
            manifest_data=workflow_manifest
        )
        
        # Execute the workflow
        result = await _execute_entity(execution_request)
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute/direct")
async def execute_direct(execution_request: ExecutionRequest):
    """
    Direct execution with full ExecutionRequest object
    """
    try:
        result = await _execute_entity(execution_request)
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute direct request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXECUTION STATUS & MONITORING
# ============================================================================

@app.get("/executions")
async def list_executions(
    status: Optional[ExecutionStatus] = None,
    entity_type: Optional[str] = None,
    limit: int = 50
):
    """List recent executions with optional filters"""
    return await app.state.registry.list_executions(
        status=status,
        entity_type=entity_type,
        limit=limit
    )


@app.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get details of a specific execution"""
    execution = await app.state.registry.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return execution


@app.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel a running execution"""
    try:
        result = await app.state.registry.cancel_execution(execution_id)
        return {"status": "cancelled" if result else "not_found", "execution_id": execution_id}
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================

async def _fetch_manifest(manifest_type: str, name: str) -> Optional[Dict[str, Any]]:
    """Fetch manifest from the ingestion service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{app.state.manifest_service_url}/registry/manifest/{manifest_type}/{name}"
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch manifest: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to manifest service: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Manifest ingestion service unavailable"
        )


async def _execute_entity(execution_request: ExecutionRequest) -> ExecutionResponse:
    """Execute an entity based on its manifest"""
    
    # Register execution start
    execution_id = await app.state.registry.register_execution(execution_request)
    
    try:
        # Determine runtime type from manifest
        runtime_type = await _determine_runtime_type(execution_request.manifest_data)
        
        # Get appropriate executor
        executor = app.state.executors.get(runtime_type)
        if not executor:
            raise ValueError(f"No executor available for runtime type: {runtime_type}")
        
        # Execute the entity
        result = await executor.execute(execution_request)
        
        # Update execution status
        await app.state.registry.update_execution(execution_id, result)
        
        return result
        
    except Exception as e:
        # Update execution with error
        error_result = ExecutionResponse(
            execution_id=execution_id,
            status=ExecutionStatus.FAILED,
            error=str(e),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        await app.state.registry.update_execution(execution_id, error_result)
        raise


async def _determine_runtime_type(manifest_data: Dict[str, Any]) -> RuntimeType:
    """Determine the runtime type based on manifest data"""
    
    # For tools, check the runtime field
    if "runtime" in manifest_data:
        runtime_str = manifest_data["runtime"]
        if runtime_str in ["python", "python3"]:
            return RuntimeType.PYTHON
        elif runtime_str in ["bash", "shell", "sh"]:
            return RuntimeType.SHELL
        elif runtime_str == "docker":
            return RuntimeType.DOCKER
    
    # For newer manifest formats, check implementation section
    if "implementation" in manifest_data:
        impl = manifest_data["implementation"]
        if "type" in impl:
            impl_type = impl["type"]
            if impl_type in ["python", "script"]:
                return RuntimeType.PYTHON
            elif impl_type in ["shell", "bash"]:
                return RuntimeType.SHELL
            elif impl_type == "docker":
                return RuntimeType.DOCKER
    
    # Default fallback
    return RuntimeType.PYTHON


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8083))
    log_level = os.getenv("LOG_LEVEL", "info").lower()  # Ensure lowercase for uvicorn
    
    logger.info(f"Starting Runtime Executor Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )