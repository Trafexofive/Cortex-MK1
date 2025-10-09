"""
==============================================================================
STORAGE BACKEND - BASE INTERFACE
==============================================================================
Abstract base class for all storage backends.
==============================================================================
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.storage_models import (
    Session, SessionCreate, SessionUpdate, SessionQuery,
    Message, MessageCreate, MessageQuery,
    AgentState, StateUpdate,
    Artifact, ArtifactCreate, ArtifactQuery,
    Metric, MetricCreate, MetricQuery,
    CacheEntry, CacheSet
)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    # ========================================================================
    # SESSION OPERATIONS
    # ========================================================================
    
    @abstractmethod
    async def create_session(self, session: SessionCreate) -> Session:
        """Create a new session."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, update: SessionUpdate) -> Optional[Session]:
        """Update session."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        pass
    
    @abstractmethod
    async def list_sessions(self, query: SessionQuery) -> List[Session]:
        """List sessions with filtering."""
        pass
    
    # ========================================================================
    # MESSAGE/HISTORY OPERATIONS
    # ========================================================================
    
    @abstractmethod
    async def add_message(self, message: MessageCreate) -> Message:
        """Add message to history."""
        pass
    
    @abstractmethod
    async def get_messages(self, query: MessageQuery) -> List[Message]:
        """Get conversation history."""
        pass
    
    @abstractmethod
    async def delete_messages(self, session_id: str) -> bool:
        """Delete all messages for a session."""
        pass
    
    # ========================================================================
    # STATE OPERATIONS
    # ========================================================================
    
    @abstractmethod
    async def get_state(self, session_id: str) -> Optional[AgentState]:
        """Get agent state."""
        pass
    
    @abstractmethod
    async def set_state(self, session_id: str, update: StateUpdate) -> AgentState:
        """Set agent state."""
        pass
    
    @abstractmethod
    async def delete_state(self, session_id: str) -> bool:
        """Delete agent state."""
        pass
    
    # ========================================================================
    # ARTIFACT OPERATIONS
    # ========================================================================
    
    @abstractmethod
    async def create_artifact(self, artifact: ArtifactCreate) -> Artifact:
        """Create artifact record."""
        pass
    
    @abstractmethod
    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID."""
        pass
    
    @abstractmethod
    async def list_artifacts(self, query: ArtifactQuery) -> List[Artifact]:
        """List artifacts."""
        pass
    
    @abstractmethod
    async def delete_artifact(self, artifact_id: str) -> bool:
        """Delete artifact."""
        pass
    
    # ========================================================================
    # METRIC OPERATIONS
    # ========================================================================
    
    @abstractmethod
    async def record_metric(self, metric: MetricCreate) -> Metric:
        """Record a metric."""
        pass
    
    @abstractmethod
    async def query_metrics(self, query: MetricQuery) -> List[Metric]:
        """Query metrics."""
        pass
    
    # ========================================================================
    # CACHE OPERATIONS
    # ========================================================================
    
    @abstractmethod
    async def cache_get(self, key: str) -> Optional[CacheEntry]:
        """Get cached value."""
        pass
    
    @abstractmethod
    async def cache_set(self, cache: CacheSet) -> CacheEntry:
        """Set cache value."""
        pass
    
    @abstractmethod
    async def cache_delete(self, key: str) -> bool:
        """Delete cache entry."""
        pass
    
    @abstractmethod
    async def cache_cleanup(self) -> int:
        """Cleanup expired cache entries. Returns number of deleted entries."""
        pass
    
    # ========================================================================
    # LIFECYCLE
    # ========================================================================
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize backend (create tables, connections, etc.)."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close backend connections."""
        pass
