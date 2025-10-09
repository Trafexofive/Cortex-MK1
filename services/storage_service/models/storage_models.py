"""
==============================================================================
STORAGE SERVICE - DATA MODELS
==============================================================================
Pydantic models for all storage types in Cortex-Prime.
==============================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class SessionStatus(str, Enum):
    """Session lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class MessageRole(str, Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class StorageType(str, Enum):
    """Storage type identifier."""
    SESSIONS = "sessions"
    HISTORY = "history"
    STATE = "state"
    ARTIFACTS = "artifacts"
    METRICS = "metrics"
    CACHE = "cache"
    LOGS = "logs"


# ============================================================================
# SESSION MODELS
# ============================================================================

class Session(BaseModel):
    """Agent conversation session."""
    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:16]}")
    agent_name: str
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionCreate(BaseModel):
    """Request to create a session."""
    agent_name: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    """Request to update a session."""
    status: Optional[SessionStatus] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# MESSAGE/HISTORY MODELS
# ============================================================================

class Message(BaseModel):
    """Conversation message."""
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:16]}")
    session_id: str
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageCreate(BaseModel):
    """Request to create a message."""
    session_id: str
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# STATE MODELS
# ============================================================================

class AgentState(BaseModel):
    """Agent memory/context/variables."""
    session_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StateUpdate(BaseModel):
    """Request to update agent state."""
    data: Dict[str, Any]


# ============================================================================
# ARTIFACT MODELS
# ============================================================================

class Artifact(BaseModel):
    """Generated file/artifact."""
    id: str = Field(default_factory=lambda: f"artifact_{uuid.uuid4().hex[:16]}")
    session_id: str
    name: str
    type: str  # pdf, image, code, etc.
    path: str  # filesystem path or S3 key
    size: int  # bytes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ArtifactCreate(BaseModel):
    """Request to create an artifact."""
    session_id: str
    name: str
    type: str
    path: str
    size: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# METRICS MODELS
# ============================================================================

class Metric(BaseModel):
    """Execution metric."""
    id: str = Field(default_factory=lambda: f"metric_{uuid.uuid4().hex[:16]}")
    entity_type: str  # agent, tool, relic
    entity_name: str
    session_id: Optional[str] = None
    metric_name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricCreate(BaseModel):
    """Request to create a metric."""
    entity_type: str
    entity_name: str
    session_id: Optional[str] = None
    metric_name: str
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# CACHE MODELS
# ============================================================================

class CacheEntry(BaseModel):
    """Cache entry with TTL."""
    key: str
    value: Dict[str, Any]
    ttl: Optional[int] = None  # seconds, None = no expiry
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl is None:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl


class CacheSet(BaseModel):
    """Request to set cache value."""
    key: str
    value: Dict[str, Any]
    ttl: Optional[int] = None  # seconds


# ============================================================================
# QUERY MODELS
# ============================================================================

class SessionQuery(BaseModel):
    """Query parameters for sessions."""
    agent_name: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[SessionStatus] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class MessageQuery(BaseModel):
    """Query parameters for messages."""
    session_id: str
    role: Optional[MessageRole] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ArtifactQuery(BaseModel):
    """Query parameters for artifacts."""
    session_id: str
    type: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class MetricQuery(BaseModel):
    """Query parameters for metrics."""
    entity_type: Optional[str] = None
    entity_name: Optional[str] = None
    session_id: Optional[str] = None
    metric_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
