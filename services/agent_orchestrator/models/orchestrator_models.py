"""
==============================================================================
AGENT ORCHESTRATOR - DATA MODELS
==============================================================================
Pydantic models for agent session orchestration.
==============================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class MessageRole(str, Enum):
    """Message role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# ============================================================================
# SESSION MODELS
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request to create an agent session."""
    agent_name: str
    user_id: Optional[str] = None
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionInfo(BaseModel):
    """Information about an agent session."""
    session_id: str
    agent_name: str
    user_id: Optional[str] = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    active_relics: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# MESSAGE MODELS
# ============================================================================

class MessageRequest(BaseModel):
    """Request to send a message to an agent."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = True


class ToolCall(BaseModel):
    """Tool call from LLM."""
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:16]}")
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Result of tool execution."""
    call_id: str
    name: str
    result: Any
    error: Optional[str] = None


class MessageResponse(BaseModel):
    """Response from agent."""
    role: MessageRole
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    """Streaming chunk."""
    type: str  # "content", "tool_call", "done", "error"
    data: Any
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
