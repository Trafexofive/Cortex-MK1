#!/usr/bin/env python3
"""
Enhanced Artifacts Management Tool
Provides robust SQLite-based artifact storage with advanced features.

Features:
- Automatic content deduplication via SHA-256 hashing
- Transparent compression for artifacts > 1KB
- Tag-based organization and filtering
- Access tracking and usage statistics
- Pagination support for large datasets
- WAL mode for concurrent access
- Automatic database maintenance (vacuum)
- Environment variable configuration
"""

import json
import os
import sys
import uuid
import sqlite3
import hashlib
import gzip
import time
import threading
import dotenv
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
import logging

# Load environment variables from .env file
dotenv.load_dotenv()

# Configuration with environment variable support
def get_env(key, default, type_converter=str):
    """Get config value from environment variable or use default."""
    env_key = f"ARTIFACTS_{key.upper()}"
    env_value = os.environ.get(env_key)
    if env_value is None:
        return default
    
    # Handle boolean conversions
    if type_converter == bool:
        return env_value.lower() in ('true', 't', '1', 'yes', 'y')
    
    # Handle other types
    try:
        return type_converter(env_value)
    except (ValueError, TypeError):
        return default

# Configuration with environment variable support
CONFIG = {
    'db_path': get_env('db_path', None),
    'db_timeout': get_env('db_timeout', 30.0, float),
    'max_retries': get_env('max_retries', 3, int),
    'compression_threshold': get_env('compression_threshold', 1024, int),
    'vacuum_threshold': get_env('vacuum_threshold', 1000, int),
    'wal_mode': get_env('wal_mode', True, bool),
    'cache_size': get_env('cache_size', 10000, int),
    'log_level': get_env('log_level', 'ERROR'),
    'merge_tags_on_duplicate': get_env('merge_tags_on_duplicate', False, bool),
}

# Setup logging
logging.basicConfig(
    level=getattr(logging, CONFIG['log_level']),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
_operation_counter = 0
_counter_lock = threading.Lock()

class ArtifactError(Exception):
    """Base exception for artifact operations."""
    pass

class ArtifactNotFoundError(ArtifactError):
    """Raised when artifact is not found."""
    pass

class ArtifactDB:
    """High-performance SQLite-based artifact storage."""
    
    def __init__(self, db_path: Path):
        """
        Initialize artifact database with the specified path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.data_dir = db_path.parent
        self._ensure_data_dir()
        self._init_database()
        
    def _ensure_data_dir(self):
        """Create data directory with proper permissions."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        except OSError as e:
            raise ArtifactError(f"Failed to create data directory: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with optimized settings."""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=CONFIG['db_timeout'],
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row
            
            # Performance optimizations
            if CONFIG['wal_mode']:
                conn.execute('PRAGMA journal_mode=WAL')
            conn.execute(f'PRAGMA cache_size={CONFIG["cache_size"]}')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA temp_store=MEMORY')
            conn.execute('PRAGMA mmap_size=268435456')  # 256MB
            
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise ArtifactError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _init_database(self):
        """Initialize database schema with optimizations."""
        schema = """
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            content BLOB,
            metadata TEXT,
            content_hash TEXT,
            size INTEGER,
            compressed BOOLEAN DEFAULT 0,
            created_at REAL,
            updated_at REAL,
            access_count INTEGER DEFAULT 0,
            last_accessed REAL
        );
        
        CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at);
        CREATE INDEX IF NOT EXISTS idx_artifacts_updated_at ON artifacts(updated_at);
        CREATE INDEX IF NOT EXISTS idx_artifacts_hash ON artifacts(content_hash);
        CREATE INDEX IF NOT EXISTS idx_artifacts_size ON artifacts(size);
        
        CREATE TABLE IF NOT EXISTS artifact_tags (
            artifact_id TEXT,
            tag TEXT,
            FOREIGN KEY(artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_tags_artifact_id ON artifact_tags(artifact_id);
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON artifact_tags(tag);
        
        CREATE TABLE IF NOT EXISTS metadata_kv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT
        );
        INSERT OR IGNORE INTO metadata_kv (key, value) VALUES 
            ('schema_version', '2.0'),
            ('created_at', ?),
            ('operation_count', '0');
        """
        
        with self._get_connection() as conn:
            conn.executescript(schema)
            conn.execute(
                'UPDATE metadata_kv SET value = ? WHERE key = "created_at" AND value IS NULL',
                (time.time(),)
            )
    
    def _compress_content(self, content: bytes) -> tuple[bytes, bool]:
        """
        Compress content if beneficial.
        
        Args:
            content: Raw content bytes
            
        Returns:
            Tuple of (possibly compressed content, is_compressed flag)
        """
        if len(content) < CONFIG['compression_threshold']:
            return content, False
        
        compressed = gzip.compress(content, compresslevel=6)
        if len(compressed) < len(content) * 0.9:  # Only if 10%+ savings
            return compressed, True
        return content, False
    
    def _decompress_content(self, content: bytes, is_compressed: bool) -> bytes:
        """
        Decompress content if needed.
        
        Args:
            content: Possibly compressed content
            is_compressed: Flag indicating if content is compressed
            
        Returns:
            Decompressed content bytes
        """
        if is_compressed:
            return gzip.decompress(content)
        return content
    
    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    def _increment_operation_counter(self):
        """Thread-safe operation counter increment."""
        global _operation_counter
        with _counter_lock:
            _operation_counter += 1
            if _operation_counter % CONFIG['vacuum_threshold'] == 0:
                self._vacuum_database()
    
    def _vacuum_database(self):
        """Vacuum database to reclaim space."""
        try:
            with self._get_connection() as conn:
                conn.execute('VACUUM')
            logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.warning(f"Vacuum failed: {e}")
    
    def _add_tags_to_artifact(self, conn, artifact_id: str, tags: List[str]) -> None:
        """
        Add tags to an artifact.
        
        Args:
            conn: Database connection
            artifact_id: ID of the artifact to tag
            tags: List of tags to add
        """
        if not tags:
            return
            
        for tag in tags:
            conn.execute(
                'INSERT OR IGNORE INTO artifact_tags (artifact_id, tag) VALUES (?, ?)',
                (artifact_id, tag.strip())
            )
    
    def _merge_tags(self, conn, artifact_id: str, tags: List[str]) -> None:
        """
        Merge new tags with existing tags on an artifact.
        
        Args:
            conn: Database connection
            artifact_id: ID of the artifact
            tags: List of new tags to merge
        """
        if not tags:
            return
            
        # Add each tag if it doesn't already exist
        for tag in tags:
            conn.execute(
                'INSERT OR IGNORE INTO artifact_tags (artifact_id, tag) VALUES (?, ?)',
                (artifact_id, tag.strip())
            )
    
    def create_artifact(self, data: Any, tags: Optional[List[str]] = None, 
                       merge_tags: Optional[bool] = None) -> str:
        """
        Create new artifact with deduplication and tagging.
        
        Args:
            data: The content to store
            tags: Optional list of tags for organization
            merge_tags: Whether to merge tags when duplicate content is found.
                        Defaults to the value in CONFIG.
                        
        Returns:
            ID of the created or existing artifact
            
        Notes:
            When duplicate content is detected (based on hash), this function
            returns the existing artifact ID. If merge_tags is True, it will
            add the new tags to the existing artifact; otherwise, it will
            silently ignore the new tags.
        """
        if merge_tags is None:
            merge_tags = CONFIG['merge_tags_on_duplicate']
            
        artifact_id = str(uuid.uuid4())
        content_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
        content_hash = self._calculate_hash(content_bytes)
        
        # Check for existing artifact with same hash
        with self._get_connection() as conn:
            existing = conn.execute(
                'SELECT id FROM artifacts WHERE content_hash = ?',
                (content_hash,)
            ).fetchone()
            
            if existing:
                existing_id = existing['id']
                logger.info(f"Duplicate content detected, referencing existing artifact: {existing_id}")
                
                # Optionally merge tags with existing artifact
                if merge_tags and tags:
                    self._merge_tags(conn, existing_id, tags)
                    logger.debug(f"Merged {len(tags)} tags with existing artifact {existing_id}")
                    
                return existing_id
        
        compressed_content, is_compressed = self._compress_content(content_bytes)
        now = time.time()
        
        with self._get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                conn.execute("""
                    INSERT INTO artifacts (
                        id, content, metadata, content_hash, size, compressed,
                        created_at, updated_at, last_accessed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    artifact_id, compressed_content, json.dumps({}), content_hash,
                    len(content_bytes), is_compressed, now, now, now
                ))
                
                # Add tags if provided
                if tags:
                    self._add_tags_to_artifact(conn, artifact_id, tags)
                
                conn.execute('COMMIT')
                self._increment_operation_counter()
                logger.debug(f"Created artifact {artifact_id} (compressed: {is_compressed})")
                return artifact_id
                
            except Exception:
                conn.execute('ROLLBACK')
                raise
    
    def read_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """
        Read artifact with access tracking.
        
        Args:
            artifact_id: UUID of the artifact to read
            
        Returns:
            Dictionary containing artifact data and metadata
            
        Raises:
            ArtifactNotFoundError: If artifact does not exist
        """
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT content, metadata, compressed, size, created_at, updated_at,
                       access_count, content_hash
                FROM artifacts WHERE id = ?
            """, (artifact_id,)).fetchone()
            
            if not row:
                raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")
            
            # Update access statistics
            now = time.time()
            conn.execute("""
                UPDATE artifacts 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            """, (now, artifact_id))
            
            # Get tags
            tags = [tag_row['tag'] for tag_row in conn.execute(
                'SELECT tag FROM artifact_tags WHERE artifact_id = ?',
                (artifact_id,)
            ).fetchall()]
            
            # Decompress and parse content
            content_bytes = self._decompress_content(row['content'], row['compressed'])
            content = json.loads(content_bytes.decode('utf-8'))
            
            return {
                'id': artifact_id,
                'content': content,
                'metadata': json.loads(row['metadata']),
                'tags': tags,
                'stats': {
                    'size': row['size'],
                    'compressed': bool(row['compressed']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'access_count': row['access_count'] + 1,
                    'content_hash': row['content_hash']
                }
            }
    
    def update_artifact(self, artifact_id: str, data: Optional[Any] = None, 
                        tags: Optional[List[str]] = None) -> bool:
        """
        Update artifact content and/or tags.
        
        Args:
            artifact_id: UUID of the artifact to update
            data: New content data (optional if only updating tags)
            tags: New list of tags (optional if only updating content)
            
        Returns:
            True if update was successful, False if artifact not found
            
        Notes:
            This method supports partial updates. You can update:
            - Only the content (provide data, set tags=None)
            - Only the tags (provide tags, set data=None)
            - Both content and tags (provide both)
        """
        now = time.time()
        
        # Check if artifact exists
        with self._get_connection() as conn:
            existing = conn.execute(
                'SELECT id FROM artifacts WHERE id = ?',
                (artifact_id,)
            ).fetchone()
            
            if not existing:
                return False
            
            conn.execute('BEGIN IMMEDIATE')
            try:
                # Update content if provided
                if data is not None:
                    content_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
                    content_hash = self._calculate_hash(content_bytes)
                    compressed_content, is_compressed = self._compress_content(content_bytes)
                    
                    conn.execute("""
                        UPDATE artifacts 
                        SET content = ?, content_hash = ?, size = ?, compressed = ?, updated_at = ?
                        WHERE id = ?
                    """, (compressed_content, content_hash, len(content_bytes), 
                          is_compressed, now, artifact_id))
                
                # Update tags if provided
                if tags is not None:
                    conn.execute('DELETE FROM artifact_tags WHERE artifact_id = ?', (artifact_id,))
                    self._add_tags_to_artifact(conn, artifact_id, tags)
                
                # If any update was performed, update the timestamp
                if data is not None or tags is not None:
                    conn.execute('UPDATE artifacts SET updated_at = ? WHERE id = ?', 
                                (now, artifact_id))
                
                conn.execute('COMMIT')
                self._increment_operation_counter()
                logger.debug(f"Updated artifact {artifact_id}")
                return True
                
            except Exception:
                conn.execute('ROLLBACK')
                raise
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete artifact and associated data.
        
        Args:
            artifact_id: UUID of the artifact to delete
            
        Returns:
            True if deletion was successful, False if artifact not found
        """
        with self._get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                # Check if exists
                existing = conn.execute(
                    'SELECT id FROM artifacts WHERE id = ?',
                    (artifact_id,)
                ).fetchone()
                
                if not existing:
                    conn.execute('ROLLBACK')
                    return False
                
                # Delete tags first (foreign key constraint)
                conn.execute('DELETE FROM artifact_tags WHERE artifact_id = ?', (artifact_id,))
                
                # Delete artifact
                conn.execute('DELETE FROM artifacts WHERE id = ?', (artifact_id,))
                
                conn.execute('COMMIT')
                self._increment_operation_counter()
                logger.debug(f"Deleted artifact {artifact_id}")
                return True
                
            except Exception:
                conn.execute('ROLLBACK')
                raise
    
    def list_artifacts(self, limit: Optional[int] = None, offset: int = 0, 
                      tag_filter: Optional[str] = None, 
                      tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        List artifacts with filtering and pagination.
        
        Args:
            limit: Maximum number of artifacts to return
            offset: Number of artifacts to skip (for pagination)
            tag_filter: Filter by a single tag (legacy parameter)
            tags: Filter by multiple tags (all tags must be present)
            
        Returns:
            Dictionary with artifact listings and pagination metadata
        """
        with self._get_connection() as conn:
            base_query = """
                SELECT a.id, a.size, a.created_at, a.updated_at, a.access_count
                FROM artifacts a
            """
            
            tag_join = ""
            where_clauses = []
            params = []
            
            # Handle tag filtering
            if tags or tag_filter:
                filter_tags = tags or [tag_filter]
                
                for i, tag in enumerate(filter_tags):
                    alias = f"t{i}"
                    tag_join += f" JOIN artifact_tags {alias} ON a.id = {alias}.artifact_id AND {alias}.tag = ?"
                    params.append(tag)
            
            # Combine query parts
            query = base_query + tag_join
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            query += " ORDER BY a.created_at DESC"
            
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            rows = conn.execute(query, params).fetchall()
            
            # Get total count with same filtering
            count_query = "SELECT COUNT(DISTINCT a.id) as total FROM artifacts a " + tag_join
            if where_clauses:
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            count_params = params[:]
            if limit is not None:
                # Remove limit and offset from count params
                count_params = count_params[:-2]
                
            total = conn.execute(count_query, count_params).fetchone()['total']
            
            # Get tags for each artifact
            artifacts = []
            for row in rows:
                artifact_id = row['id']
                tags = [tag_row['tag'] for tag_row in conn.execute(
                    'SELECT tag FROM artifact_tags WHERE artifact_id = ?',
                    (artifact_id,)
                ).fetchall()]
                
                artifacts.append({
                    'id': artifact_id,
                    'size': row['size'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'access_count': row['access_count'],
                    'tags': tags
                })
            
            return {
                'artifacts': artifacts,
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + len(artifacts) < total
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dictionary with database statistics and metrics
        """
        with self._get_connection() as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_artifacts,
                    SUM(size) as total_size,
                    AVG(size) as avg_size,
                    SUM(CASE WHEN compressed THEN 1 ELSE 0 END) as compressed_count,
                    SUM(access_count) as total_accesses,
                    MIN(created_at) as oldest_artifact,
                    MAX(created_at) as newest_artifact
                FROM artifacts
            """).fetchone()
            
            tag_count = conn.execute(
                'SELECT COUNT(DISTINCT tag) as tag_count FROM artifact_tags'
            ).fetchone()['tag_count']
            
            return {
                'total_artifacts': stats['total_artifacts'],
                'total_size_bytes': stats['total_size'] or 0,
                'average_size_bytes': stats['avg_size'] or 0,
                'compressed_artifacts': stats['compressed_count'],
                'total_accesses': stats['total_accesses'] or 0,
                'unique_tags': tag_count,
                'oldest_artifact': stats['oldest_artifact'],
                'newest_artifact': stats['newest_artifact'],
                'database_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0
            }

def get_db_path() -> Path:
    """Determine database path from configuration or defaults."""
    # First, check if a custom path is set in configuration
    if CONFIG['db_path']:
        db_path = Path(CONFIG['db_path'])
        if not db_path.is_absolute():
            # If path is relative, make it relative to the script
            script_dir = Path(__file__).parent.absolute()
            db_path = script_dir.parent / db_path
        return db_path
        
    # Default: relative to script location
    script_dir = Path(__file__).parent.absolute()
    data_dir = script_dir.parent / ".data"
    return data_dir / "artifacts.db"

def main():
    """Main entry point with enhanced error handling and features."""
    try:
        # Initialize database
        db_path = get_db_path()
        db = ArtifactDB(db_path)
        
        if len(sys.argv) < 2:
            print(json.dumps({
                "error": "Operation type required",
                "success": False,
                "usage": "Supported operations: create, read, update, delete, list, stats"
            }))
            sys.exit(1)
        
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error": f"Invalid JSON parameters: {e}",
                "success": False
            }))
            sys.exit(1)
        
        operation = params.get("operation")
        if not operation:
            print(json.dumps({
                "error": "'operation' parameter missing",
                "success": False
            }))
            sys.exit(1)
        
        # Execute operations
        if operation == "create":
            data = params.get("data")
            if data is None:
                print(json.dumps({
                    "error": "'data' required for create operation",
                    "success": False
                }))
                sys.exit(1)
            
            tags = params.get("tags", [])
            merge_tags = params.get("merge_tags", None)
            artifact_id = db.create_artifact(data, tags, merge_tags)
            print(json.dumps({
                "artifact_id": artifact_id,
                "success": True,
                "operation": "create"
            }))
        
        elif operation == "read":
            artifact_id = params.get("artifact_id")
            if not artifact_id:
                print(json.dumps({
                    "error": "'artifact_id' required for read operation",
                    "success": False
                }))
                sys.exit(1)
            
            try:
                artifact = db.read_artifact(artifact_id)
                artifact["success"] = True
                print(json.dumps(artifact))
            except ArtifactNotFoundError:
                print(json.dumps({
                    "error": "Artifact not found",
                    "success": False,
                    "error_type": "ArtifactNotFoundError",
                    "artifact_id": artifact_id
                }))
        
        elif operation == "update":
            artifact_id = params.get("artifact_id")
            if not artifact_id:
                print(json.dumps({
                    "error": "'artifact_id' required for update operation",
                    "success": False
                }))
                sys.exit(1)
            
            # Both data and tags are now optional
            data = params.get("data")
            tags = params.get("tags")
            
            # Ensure at least one of data or tags is provided
            if data is None and tags is None:
                print(json.dumps({
                    "error": "At least one of 'data' or 'tags' must be provided for update operation",
                    "success": False
                }))
                sys.exit(1)
            
            success = db.update_artifact(artifact_id, data, tags)
            print(json.dumps({
                "success": success,
                "operation": "update",
                "artifact_id": artifact_id
            }))
        
        elif operation == "delete":
            artifact_id = params.get("artifact_id")
            if not artifact_id:
                print(json.dumps({
                    "error": "'artifact_id' required for delete operation",
                    "success": False
                }))
                sys.exit(1)
            
            success = db.delete_artifact(artifact_id)
            print(json.dumps({
                "success": success,
                "operation": "delete",
                "artifact_id": artifact_id
            }))
        
        elif operation == "list":
            limit = params.get("limit")
            offset = params.get("offset", 0)
            tag_filter = params.get("tag")
            tags = params.get("tags")
            
            result = db.list_artifacts(limit, offset, tag_filter, tags)
            result["success"] = True
            result["operation"] = "list"
            print(json.dumps(result))
        
        elif operation == "stats":
            stats = db.get_stats()
            stats["success"] = True
            stats["operation"] = "stats"
            print(json.dumps(stats))
        
        else:
            print(json.dumps({
                "error": f"Unknown operation '{operation}'",
                "success": False,
                "supported_operations": ["create", "read", "update", "delete", "list", "stats"]
            }))
            sys.exit(1)
    
    except ArtifactError as e:
        print(json.dumps({
            "error": str(e),
            "success": False,
            "error_type": "ArtifactError"
        }))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error")
        print(json.dumps({
            "error": f"Unexpected error: {e}",
            "success": False,
            "error_type": "UnexpectedError"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
