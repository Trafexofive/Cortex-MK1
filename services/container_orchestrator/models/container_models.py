"""
==============================================================================
CONTAINER ORCHESTRATOR - DATA MODELS
==============================================================================
Pydantic models for Docker container management.
==============================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ContainerStatus(str, Enum):
    """Container status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    EXITED = "exited"
    DEAD = "dead"


# ============================================================================
# RESOURCE LIMITS
# ============================================================================

class ResourceLimits(BaseModel):
    """Resource limits for container execution."""
    memory_mb: int = Field(default=512, ge=64, le=8192)
    cpu_limit: float = Field(default=1.0, ge=0.1, le=8.0)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    disk_mb: Optional[int] = Field(default=None, ge=100, le=10240)


# ============================================================================
# TOOL EXECUTION MODELS
# ============================================================================

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool in a container."""
    tool_name: str
    session_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Container configuration
    image: Optional[str] = None  # Docker image, if None will build from manifest
    dockerfile: Optional[str] = None  # Path to Dockerfile
    build_context: Optional[str] = None  # Build context path
    
    # Runtime configuration
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: Dict[str, str] = Field(default_factory=dict)  # host_path: container_path
    
    # Network
    network_mode: str = "bridge"  # bridge, host, none, or custom network name
    
    # Cleanup
    cleanup: bool = True  # Remove container after execution


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:16]}")
    tool_name: str
    session_id: str
    
    status: ExecutionStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Results
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    result: Optional[Dict[str, Any]] = None  # Parsed tool output
    
    # Container info
    container_id: Optional[str] = None
    
    # Resource usage
    execution_time_seconds: Optional[float] = None
    memory_used_mb: Optional[float] = None
    
    # Error info
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# RELIC MODELS
# ============================================================================

class RelicStartRequest(BaseModel):
    """Request to start a relic container."""
    relic_name: str
    session_id: str
    
    # Container configuration
    image: Optional[str] = None  # Docker image
    dockerfile: Optional[str] = None  # Path to Dockerfile
    build_context: Optional[str] = None
    
    # Runtime configuration
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: Dict[str, str] = Field(default_factory=dict)
    
    # Port mappings for relic API
    ports: Dict[int, int] = Field(default_factory=dict)  # host_port: container_port
    
    # Network isolation
    create_private_network: bool = True  # Create private network for session
    
    # Health check
    health_check_endpoint: str = "/health"
    health_check_interval_seconds: int = 10
    health_check_timeout_seconds: int = 30


class RelicInfo(BaseModel):
    """Information about a running relic."""
    relic_id: str = Field(default_factory=lambda: f"relic_{uuid.uuid4().hex[:16]}")
    relic_name: str
    session_id: str
    
    status: ContainerStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Container info
    container_id: str
    container_name: str
    
    # Network info
    network_id: Optional[str] = None
    network_name: Optional[str] = None
    internal_url: Optional[str] = None  # URL accessible from agent container
    
    # Health
    healthy: bool = False
    last_health_check: Optional[datetime] = None
    
    # Resource usage
    memory_used_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# CONTAINER STATS
# ============================================================================

class ContainerStats(BaseModel):
    """Container resource statistics."""
    container_id: str
    name: str
    
    # Status
    status: ContainerStatus
    running: bool
    
    # CPU
    cpu_percent: float = 0.0
    
    # Memory
    memory_used_mb: float = 0.0
    memory_limit_mb: float = 0.0
    memory_percent: float = 0.0
    
    # Network
    network_rx_mb: float = 0.0
    network_tx_mb: float = 0.0
    
    # Disk
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    
    # Timestamps
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# CLEANUP MODELS
# ============================================================================

class SessionCleanupRequest(BaseModel):
    """Request to cleanup all containers for a session."""
    session_id: str
    force: bool = False  # Force remove even if running


class SessionCleanupResult(BaseModel):
    """Result of session cleanup."""
    session_id: str
    containers_removed: int
    networks_removed: int
    volumes_removed: int
    errors: List[str] = Field(default_factory=list)
