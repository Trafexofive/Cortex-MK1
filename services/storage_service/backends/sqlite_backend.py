"""
==============================================================================
STORAGE BACKEND - SQLITE IMPLEMENTATION
==============================================================================
SQLite backend for storage service with async support.
==============================================================================
"""

import aiosqlite
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from .base_backend import StorageBackend
from models.storage_models import (
    Session, SessionCreate, SessionUpdate, SessionQuery, SessionStatus,
    Message, MessageCreate, MessageQuery, MessageRole,
    AgentState, StateUpdate,
    Artifact, ArtifactCreate, ArtifactQuery,
    Metric, MetricCreate, MetricQuery,
    CacheEntry, CacheSet
)


class SQLiteBackend(StorageBackend):
    """SQLite storage backend."""
    
    def __init__(self, db_path: str = "/data/storage.db"):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
    
    # ========================================================================
    # LIFECYCLE
    # ========================================================================
    
    async def initialize(self) -> None:
        """Initialize SQLite database and create tables."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        
        # Create tables
        await self._create_tables()
        
        logger.info(f"✅ SQLite backend initialized: {self.db_path}")
    
    async def close(self) -> None:
        """Close database connection."""
        if self.db:
            await self.db.close()
            logger.info("SQLite backend closed")
    
    async def _create_tables(self) -> None:
        """Create all storage tables."""
        
        # Sessions table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # History table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # State table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS state (
                session_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Artifacts table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                path TEXT NOT NULL,
                size INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Metrics table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                session_id TEXT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                labels TEXT
            )
        """)
        
        # Cache table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                ttl INTEGER,
                created_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL
            )
        """)
        
        # Create indexes
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_name)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_history_session ON history(session_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_entity ON metrics(entity_type, entity_name)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id)")
        
        await self.db.commit()
    
    # ========================================================================
    # SESSION OPERATIONS
    # ========================================================================
    
    async def create_session(self, session: SessionCreate) -> Session:
        """Create a new session."""
        new_session = Session(
            agent_name=session.agent_name,
            user_id=session.user_id,
            metadata=session.metadata
        )
        
        await self.db.execute(
            """INSERT INTO sessions (id, agent_name, user_id, created_at, updated_at, status, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                new_session.id,
                new_session.agent_name,
                new_session.user_id,
                new_session.created_at.isoformat(),
                new_session.updated_at.isoformat(),
                new_session.status.value,
                json.dumps(new_session.metadata)
            )
        )
        await self.db.commit()
        
        logger.info(f"Created session: {new_session.id} for agent: {new_session.agent_name}")
        return new_session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        return Session(
            id=row["id"],
            agent_name=row["agent_name"],
            user_id=row["user_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=SessionStatus(row["status"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
    
    async def update_session(self, session_id: str, update: SessionUpdate) -> Optional[Session]:
        """Update session."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        if update.status:
            session.status = update.status
        if update.metadata is not None:
            session.metadata.update(update.metadata)
        
        session.updated_at = datetime.utcnow()
        
        await self.db.execute(
            """UPDATE sessions 
               SET status = ?, metadata = ?, updated_at = ?
               WHERE id = ?""",
            (
                session.status.value,
                json.dumps(session.metadata),
                session.updated_at.isoformat(),
                session_id
            )
        )
        await self.db.commit()
        
        logger.info(f"Updated session: {session_id}")
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and all related data."""
        cursor = await self.db.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )
        await self.db.commit()
        
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted session: {session_id}")
        return deleted
    
    async def list_sessions(self, query: SessionQuery) -> List[Session]:
        """List sessions with filtering."""
        sql = "SELECT * FROM sessions WHERE 1=1"
        params = []
        
        if query.agent_name:
            sql += " AND agent_name = ?"
            params.append(query.agent_name)
        
        if query.user_id:
            sql += " AND user_id = ?"
            params.append(query.user_id)
        
        if query.status:
            sql += " AND status = ?"
            params.append(query.status.value)
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([query.limit, query.offset])
        
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        
        return [
            Session(
                id=row["id"],
                agent_name=row["agent_name"],
                user_id=row["user_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                status=SessionStatus(row["status"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )
            for row in rows
        ]
    
    # ========================================================================
    # MESSAGE/HISTORY OPERATIONS
    # ========================================================================
    
    async def add_message(self, message: MessageCreate) -> Message:
        """Add message to history."""
        new_message = Message(
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata
        )
        
        await self.db.execute(
            """INSERT INTO history (id, session_id, role, content, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                new_message.id,
                new_message.session_id,
                new_message.role.value,
                new_message.content,
                new_message.timestamp.isoformat(),
                json.dumps(new_message.metadata)
            )
        )
        await self.db.commit()
        
        # Update session updated_at
        await self.db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), message.session_id)
        )
        await self.db.commit()
        
        return new_message
    
    async def get_messages(self, query: MessageQuery) -> List[Message]:
        """Get conversation history."""
        sql = "SELECT * FROM history WHERE session_id = ?"
        params = [query.session_id]
        
        if query.role:
            sql += " AND role = ?"
            params.append(query.role.value)
        
        sql += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([query.limit, query.offset])
        
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        
        return [
            Message(
                id=row["id"],
                session_id=row["session_id"],
                role=MessageRole(row["role"]),
                content=row["content"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )
            for row in rows
        ]
    
    async def delete_messages(self, session_id: str) -> bool:
        """Delete all messages for a session."""
        cursor = await self.db.execute(
            "DELETE FROM history WHERE session_id = ?",
            (session_id,)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    # ========================================================================
    # STATE OPERATIONS
    # ========================================================================
    
    async def get_state(self, session_id: str) -> Optional[AgentState]:
        """Get agent state."""
        cursor = await self.db.execute(
            "SELECT * FROM state WHERE session_id = ?",
            (session_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        return AgentState(
            session_id=row["session_id"],
            data=json.loads(row["data"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
    
    async def set_state(self, session_id: str, update: StateUpdate) -> AgentState:
        """Set agent state."""
        state = AgentState(
            session_id=session_id,
            data=update.data,
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(
            """INSERT OR REPLACE INTO state (session_id, data, updated_at)
               VALUES (?, ?, ?)""",
            (
                state.session_id,
                json.dumps(state.data),
                state.updated_at.isoformat()
            )
        )
        await self.db.commit()
        
        return state
    
    async def delete_state(self, session_id: str) -> bool:
        """Delete agent state."""
        cursor = await self.db.execute(
            "DELETE FROM state WHERE session_id = ?",
            (session_id,)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    # ========================================================================
    # ARTIFACT OPERATIONS
    # ========================================================================
    
    async def create_artifact(self, artifact: ArtifactCreate) -> Artifact:
        """Create artifact record."""
        new_artifact = Artifact(
            session_id=artifact.session_id,
            name=artifact.name,
            type=artifact.type,
            path=artifact.path,
            size=artifact.size,
            metadata=artifact.metadata
        )
        
        await self.db.execute(
            """INSERT INTO artifacts (id, session_id, name, type, path, size, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_artifact.id,
                new_artifact.session_id,
                new_artifact.name,
                new_artifact.type,
                new_artifact.path,
                new_artifact.size,
                new_artifact.created_at.isoformat(),
                json.dumps(new_artifact.metadata)
            )
        )
        await self.db.commit()
        
        return new_artifact
    
    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM artifacts WHERE id = ?",
            (artifact_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        return Artifact(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            type=row["type"],
            path=row["path"],
            size=row["size"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
    
    async def list_artifacts(self, query: ArtifactQuery) -> List[Artifact]:
        """List artifacts."""
        sql = "SELECT * FROM artifacts WHERE session_id = ?"
        params = [query.session_id]
        
        if query.type:
            sql += " AND type = ?"
            params.append(query.type)
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([query.limit, query.offset])
        
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        
        return [
            Artifact(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                type=row["type"],
                path=row["path"],
                size=row["size"],
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )
            for row in rows
        ]
    
    async def delete_artifact(self, artifact_id: str) -> bool:
        """Delete artifact."""
        cursor = await self.db.execute(
            "DELETE FROM artifacts WHERE id = ?",
            (artifact_id,)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    # ========================================================================
    # METRIC OPERATIONS
    # ========================================================================
    
    async def record_metric(self, metric: MetricCreate) -> Metric:
        """Record a metric."""
        new_metric = Metric(
            entity_type=metric.entity_type,
            entity_name=metric.entity_name,
            session_id=metric.session_id,
            metric_name=metric.metric_name,
            value=metric.value,
            labels=metric.labels
        )
        
        await self.db.execute(
            """INSERT INTO metrics (id, entity_type, entity_name, session_id, metric_name, value, timestamp, labels)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_metric.id,
                new_metric.entity_type,
                new_metric.entity_name,
                new_metric.session_id,
                new_metric.metric_name,
                new_metric.value,
                new_metric.timestamp.isoformat(),
                json.dumps(new_metric.labels)
            )
        )
        await self.db.commit()
        
        return new_metric
    
    async def query_metrics(self, query: MetricQuery) -> List[Metric]:
        """Query metrics."""
        sql = "SELECT * FROM metrics WHERE 1=1"
        params = []
        
        if query.entity_type:
            sql += " AND entity_type = ?"
            params.append(query.entity_type)
        
        if query.entity_name:
            sql += " AND entity_name = ?"
            params.append(query.entity_name)
        
        if query.session_id:
            sql += " AND session_id = ?"
            params.append(query.session_id)
        
        if query.metric_name:
            sql += " AND metric_name = ?"
            params.append(query.metric_name)
        
        if query.start_time:
            sql += " AND timestamp >= ?"
            params.append(query.start_time.isoformat())
        
        if query.end_time:
            sql += " AND timestamp <= ?"
            params.append(query.end_time.isoformat())
        
        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([query.limit, query.offset])
        
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        
        return [
            Metric(
                id=row["id"],
                entity_type=row["entity_type"],
                entity_name=row["entity_name"],
                session_id=row["session_id"],
                metric_name=row["metric_name"],
                value=row["value"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                labels=json.loads(row["labels"]) if row["labels"] else {}
            )
            for row in rows
        ]
    
    # ========================================================================
    # CACHE OPERATIONS
    # ========================================================================
    
    async def cache_get(self, key: str) -> Optional[CacheEntry]:
        """Get cached value."""
        cursor = await self.db.execute(
            "SELECT * FROM cache WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        entry = CacheEntry(
            key=row["key"],
            value=json.loads(row["value"]),
            ttl=row["ttl"],
            created_at=datetime.fromisoformat(row["created_at"]),
            accessed_at=datetime.fromisoformat(row["accessed_at"])
        )
        
        # Check if expired
        if entry.is_expired():
            await self.cache_delete(key)
            return None
        
        # Update accessed_at
        await self.db.execute(
            "UPDATE cache SET accessed_at = ? WHERE key = ?",
            (datetime.utcnow().isoformat(), key)
        )
        await self.db.commit()
        
        return entry
    
    async def cache_set(self, cache: CacheSet) -> CacheEntry:
        """Set cache value."""
        entry = CacheEntry(
            key=cache.key,
            value=cache.value,
            ttl=cache.ttl
        )
        
        await self.db.execute(
            """INSERT OR REPLACE INTO cache (key, value, ttl, created_at, accessed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                entry.key,
                json.dumps(entry.value),
                entry.ttl,
                entry.created_at.isoformat(),
                entry.accessed_at.isoformat()
            )
        )
        await self.db.commit()
        
        return entry
    
    async def cache_delete(self, key: str) -> bool:
        """Delete cache entry."""
        cursor = await self.db.execute(
            "DELETE FROM cache WHERE key = ?",
            (key,)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def cache_cleanup(self) -> int:
        """Cleanup expired cache entries."""
        # Get all entries with TTL
        cursor = await self.db.execute(
            "SELECT key, created_at, ttl FROM cache WHERE ttl IS NOT NULL"
        )
        rows = await cursor.fetchall()
        
        deleted = 0
        now = datetime.utcnow()
        
        for row in rows:
            created_at = datetime.fromisoformat(row["created_at"])
            ttl = row["ttl"]
            age = (now - created_at).total_seconds()
            
            if age > ttl:
                await self.cache_delete(row["key"])
                deleted += 1
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired cache entries")
        
        return deleted
