"""
==============================================================================
EXECUTION MODELS v1.0
==============================================================================
Pydantic models for runtime execution requests, responses, and metadata.
==============================================================================
"""

import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class RuntimeType(str, Enum):
    PYTHON = "python"
    SHELL = "shell" 
    DOCKER = "docker"
    NODE = "node"
    GO = "go"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SecurityLevel(str, Enum):
    TRUSTED = "trusted"      # Full system access
    SANDBOXED = "sandboxed"  # Limited system access
    ISOLATED = "isolated"    # No system access, container only


# ============================================================================
# RESOURCE AND SECURITY MODELS
# ============================================================================

class ResourceLimits(BaseModel):
    """Resource constraints for execution"""
    max_memory_mb: Optional[int] = Field(default=512, description="Maximum memory in MB")
    max_cpu_percent: Optional[int] = Field(default=50, description="Maximum CPU usage %")
    max_execution_time_seconds: Optional[int] = Field(default=300, description="Maximum execution time")
    max_file_size_mb: Optional[int] = Field(default=100, description="Maximum file size in MB")
    max_network_requests: Optional[int] = Field(default=10, description="Maximum network requests")
    allowed_file_paths: List[str] = Field(default_factory=list, description="Allowed file system paths")
    

class ExecutionContext(BaseModel):
    """Context information for execution"""
    user_id: Optional[str] = Field(default=None, description="User initiating execution")
    session_id: Optional[str] = Field(default=None, description="Session identifier") 
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request ID")
    security_level: SecurityLevel = Field(default=SecurityLevel.SANDBOXED)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    working_directory: Optional[str] = Field(default=None)
    timeout_seconds: Optional[int] = Field(default=300)


# ============================================================================
# EXECUTION REQUEST/RESPONSE MODELS
# ============================================================================

class ExecutionRequest(BaseModel):
    """Request to execute an entity"""
    entity_type: str = Field(..., description="Type of entity (agent, tool, workflow)")
    entity_name: str = Field(..., description="Name of entity to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for execution")
    context: ExecutionContext = Field(default_factory=ExecutionContext)
    manifest_data: Dict[str, Any] = Field(..., description="Complete manifest definition")
    
    # Optional overrides
    runtime_override: Optional[RuntimeType] = Field(default=None, description="Override runtime type")
    script_path_override: Optional[str] = Field(default=None, description="Override script path")


class ExecutionResponse(BaseModel):
    """Response from an execution"""
    execution_id: str = Field(..., description="Unique execution identifier")
    status: ExecutionStatus = Field(..., description="Execution status")
    
    # Execution metadata
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")
    duration_seconds: Optional[float] = Field(default=None, description="Execution duration")
    
    # Results
    output: Optional[Any] = Field(default=None, description="Execution output/result")
    stdout: Optional[str] = Field(default=None, description="Standard output")
    stderr: Optional[str] = Field(default=None, description="Standard error")
    exit_code: Optional[int] = Field(default=None, description="Process exit code")
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(default=None, description="Type of error")
    
    # Resource usage
    memory_used_mb: Optional[float] = Field(default=None, description="Memory used in MB")
    cpu_time_seconds: Optional[float] = Field(default=None, description="CPU time used")
    
    # Additional metadata
    runtime_type: Optional[RuntimeType] = Field(default=None, description="Runtime used")
    script_path: Optional[str] = Field(default=None, description="Script path executed")
    artifacts: List[str] = Field(default_factory=list, description="Generated artifacts/files")


class ExecutionSummary(BaseModel):
    """Summary of an execution for listing"""
    execution_id: str
    entity_type: str
    entity_name: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    user_id: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# EXECUTOR CAPABILITY MODELS
# ============================================================================

class ExecutorCapabilities(BaseModel):
    """Capabilities of a runtime executor"""
    runtime_type: RuntimeType
    supported_languages: List[str] = Field(default_factory=list)
    supports_isolation: bool = Field(default=True)
    supports_resource_limits: bool = Field(default=True)
    supports_networking: bool = Field(default=False)
    supports_file_system: bool = Field(default=True)
    max_memory_mb: Optional[int] = Field(default=None)
    max_execution_time_seconds: Optional[int] = Field(default=None)


class ExecutorStatus(BaseModel):
    """Status of a runtime executor"""
    available: bool = Field(default=True)
    active_executions: int = Field(default=0)
    max_concurrent_executions: int = Field(default=10)
    total_executions: int = Field(default=0)
    successful_executions: int = Field(default=0) 
    failed_executions: int = Field(default=0)
    average_execution_time_seconds: Optional[float] = Field(default=None)
    last_execution_at: Optional[datetime] = Field(default=None)


# ============================================================================
# WORKFLOW EXECUTION MODELS
# ============================================================================

class WorkflowStepResult(BaseModel):
    """Result of a single workflow step"""
    step_name: str
    step_type: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_id: Optional[str] = None


class WorkflowExecutionResult(BaseModel):
    """Result of a complete workflow execution"""
    workflow_name: str
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[WorkflowStepResult] = Field(default_factory=list)
    final_output: Optional[Any] = None
    error: Optional[str] = None


# ============================================================================
# BATCH EXECUTION MODELS
# ============================================================================

class BatchExecutionRequest(BaseModel):
    """Request to execute multiple entities"""
    requests: List[ExecutionRequest] = Field(..., min_items=1, max_items=100)
    execution_mode: str = Field(default="parallel", description="serial or parallel")
    max_concurrent: int = Field(default=5, description="Max concurrent executions")
    stop_on_first_failure: bool = Field(default=False)


class BatchExecutionResponse(BaseModel):
    """Response from batch execution"""
    batch_id: str = Field(..., description="Unique batch identifier")
    total_requests: int
    completed_requests: int
    successful_requests: int
    failed_requests: int
    results: List[ExecutionResponse] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ExecutionStatus