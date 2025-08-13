#!/usr/bin/env python3
"""
History Tool - Universal Agent Memory System
Provides persistent storage and retrieval of agent activities with full-text search,
tagging, and analytics capabilities.
"""

import json
import os
import sys
import time
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re

# Configuration Constants
# DATA_DIR = Path(os.getenv("AGENT_WORKSPACE", ".")) / ".data"
DATA_DIR = Path(__file__).resolve().parent.parent / ".data"
DB_PATH = DATA_DIR / "history.db"
CACHE_DURATION = 300  # 5 minutes
MAX_SEARCH_RESULTS = 1000
DEFAULT_RETENTION_DAYS = 90

class HistoryError(Exception):
    """Base exception for history-specific errors."""
    pass

class ValidationError(HistoryError):
    """Parameter validation errors."""
    pass

class DatabaseError(HistoryError):
    """Database operation errors."""
    pass

def ensure_data_dir():
    """Create data directory structure if it doesn't exist."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        debug_log(f"Data directory ensured: {DATA_DIR}")
    except Exception as e:
        raise DatabaseError(f"Failed to create data directory: {e}")

def debug_log(message: str, level: str = "INFO"):
    """Centralized logging with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # Write to stderr to avoid interfering with JSON output
    print(log_entry, file=sys.stderr)
    
    # Also write to log file if possible
    try:
        log_file = DATA_DIR / "history.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception:
        pass  # Ignore logging errors

def init_database():
    """Initialize database with proper schema and indexes."""
    ensure_data_dir()
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            
            # Main history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    context_json TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            """)
            
            # Tags table for efficient tag operations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (history_id) REFERENCES history (id) ON DELETE CASCADE
                )
            """)
            
            # Statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration_ms INTEGER,
                    parameters_hash TEXT,
                    error_type TEXT
                )
            """)
            
            # Search cache for performance
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query_data TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_history_type ON history(type)",
                "CREATE INDEX IF NOT EXISTS idx_history_hash ON history(content_hash)",
                "CREATE INDEX IF NOT EXISTS idx_tags_history_id ON tags(history_id)",
                "CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)",
                "CREATE INDEX IF NOT EXISTS idx_stats_operation ON stats(operation, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_cache_expires ON search_cache(expires_at)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            # Enable full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS history_fts USING fts5(
                    content, content='history', content_rowid='id'
                )
            """)
            
            # Create triggers to maintain FTS index
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS history_fts_insert AFTER INSERT ON history
                BEGIN
                    INSERT INTO history_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS history_fts_delete AFTER DELETE ON history
                BEGIN
                    INSERT INTO history_fts(history_fts, rowid, content) VALUES('delete', old.id, old.content);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS history_fts_update AFTER UPDATE ON history
                BEGIN
                    INSERT INTO history_fts(history_fts, rowid, content) VALUES('delete', old.id, old.content);
                    INSERT INTO history_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)
            
            conn.commit()
            debug_log("Database initialized successfully")
            
    except sqlite3.Error as e:
        raise DatabaseError(f"Database initialization failed: {e}")

def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize input parameters."""
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    operation = params.get("operation")
    if not operation:
        raise ValidationError("Operation is required")
    
    valid_operations = ["add", "search", "list", "stats", "export", "cleanup", "health"]
    if operation not in valid_operations:
        raise ValidationError(f"Invalid operation. Must be one of: {valid_operations}")
    
    # Validate operation-specific parameters
    if operation == "add":
        data = params.get("data")
        if not data or not isinstance(data, dict):
            raise ValidationError("Data object is required for add operation")
        
        if not data.get("type"):
            raise ValidationError("Data type is required")
        
        if not data.get("content"):
            raise ValidationError("Data content is required")
    
    elif operation == "search":
        query = params.get("query")
        if not query or not isinstance(query, str):
            raise ValidationError("Query string is required for search operation")
    
    elif operation == "cleanup":
        days = params.get("days", DEFAULT_RETENTION_DAYS)
        if not isinstance(days, int) or days < 1:
            raise ValidationError("Days must be a positive integer")
    
    return params

def record_operation(operation: str, success: bool, duration_ms: int, 
                    params_hash: str = None, error_type: str = None):
    """Record operation statistics."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO stats (operation, timestamp, success, duration_ms, parameters_hash, error_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (operation, int(time.time()), success, duration_ms, params_hash, error_type))
            conn.commit()
    except Exception as e:
        debug_log(f"Failed to record operation stats: {e}", "ERROR")

def generate_hash(data: str) -> str:
    """Generate SHA-256 hash for data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def add_entry(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new history entry."""
    start_time = time.time()
    
    try:
        data = params["data"]
        content = str(data["content"])
        entry_type = str(data["type"])
        context = data.get("context", {})
        tags = data.get("tags", [])
        
        # Generate content hash for deduplication
        content_hash = generate_hash(f"{entry_type}:{content}")
        
        # Current timestamp
        now = int(time.time())
        
        with sqlite3.connect(DB_PATH) as conn:
            # Check for duplicate content
            existing = conn.execute(
                "SELECT id FROM history WHERE content_hash = ? AND type = ?",
                (content_hash, entry_type)
            ).fetchone()
            
            if existing:
                debug_log(f"Duplicate entry detected, updating existing ID: {existing[0]}")
                # Update existing entry
                conn.execute("""
                    UPDATE history 
                    SET context_json = ?, updated_at = ?
                    WHERE id = ?
                """, (json.dumps(context), now, existing[0]))
                entry_id = existing[0]
            else:
                # Insert new entry
                cursor = conn.execute("""
                    INSERT INTO history (timestamp, type, content, content_hash, context_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (now, entry_type, content, content_hash, json.dumps(context), now, now))
                entry_id = cursor.lastrowid
            
            # Handle tags
            if tags:
                # Remove existing tags for this entry
                conn.execute("DELETE FROM tags WHERE history_id = ?", (entry_id,))
                
                # Add new tags
                for tag in tags:
                    if tag and isinstance(tag, str):
                        conn.execute(
                            "INSERT INTO tags (history_id, tag) VALUES (?, ?)",
                            (entry_id, tag.strip().lower())
                        )
            
            conn.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("add", True, duration_ms)
        
        debug_log(f"Added history entry ID: {entry_id}")
        
        return {
            "success": True,
            "entry_id": entry_id,
            "content_hash": content_hash,
            "message": "Entry added successfully"
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("add", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"Failed to add entry: {e}")

def search_entries(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search history entries with full-text search and filters."""
    start_time = time.time()
    
    try:
        query = params["query"]
        filters = params.get("filters", {})
        limit = min(filters.get("limit", 50), MAX_SEARCH_RESULTS)
        
        # Build query hash for caching
        query_data = {
            "query": query,
            "filters": filters,
            "limit": limit
        }
        query_hash = generate_hash(json.dumps(query_data, sort_keys=True))
        
        # Check cache first
        with sqlite3.connect(DB_PATH) as conn:
            cached = conn.execute("""
                SELECT result_data FROM search_cache 
                WHERE query_hash = ? AND expires_at > ?
            """, (query_hash, int(time.time()))).fetchone()
            
            if cached:
                debug_log("Returning cached search results")
                conn.execute("""
                    UPDATE search_cache 
                    SET access_count = access_count + 1 
                    WHERE query_hash = ?
                """, (query_hash,))
                conn.commit()
                
                duration_ms = int((time.time() - start_time) * 1000)
                record_operation("search", True, duration_ms)
                
                return json.loads(cached[0])
        
        # Perform actual search
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build SQL query
            sql_parts = []
            params_list = []
            
            # Full-text search
            if query.strip():
                sql_parts.append("""
                    SELECT h.*, GROUP_CONCAT(t.tag) as tags
                    FROM history h
                    LEFT JOIN tags t ON h.id = t.history_id
                    INNER JOIN history_fts fts ON h.id = fts.rowid
                    WHERE fts.content MATCH ?
                """)
                params_list.append(query)
            else:
                sql_parts.append("""
                    SELECT h.*, GROUP_CONCAT(t.tag) as tags
                    FROM history h
                    LEFT JOIN tags t ON h.id = t.history_id
                    WHERE 1=1
                """)
            
            # Apply filters
            if filters.get("type"):
                sql_parts.append("AND h.type = ?")
                params_list.append(filters["type"])
            
            if filters.get("start_time"):
                try:
                    start_ts = int(datetime.fromisoformat(filters["start_time"]).timestamp())
                    sql_parts.append("AND h.timestamp >= ?")
                    params_list.append(start_ts)
                except ValueError:
                    raise ValidationError("Invalid start_time format")
            
            if filters.get("end_time"):
                try:
                    end_ts = int(datetime.fromisoformat(filters["end_time"]).timestamp())
                    sql_parts.append("AND h.timestamp <= ?")
                    params_list.append(end_ts)
                except ValueError:
                    raise ValidationError("Invalid end_time format")
            
            if filters.get("tags"):
                tag_conditions = []
                for tag in filters["tags"]:
                    tag_conditions.append("t.tag = ?")
                    params_list.append(tag.lower())
                if tag_conditions:
                    sql_parts.append(f"AND ({' OR '.join(tag_conditions)})")
            
            # Complete query
            sql = " ".join(sql_parts)
            sql += " GROUP BY h.id ORDER BY h.timestamp DESC LIMIT ?"
            params_list.append(limit)
            
            cursor = conn.execute(sql, params_list)
            rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                entry = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "type": row["type"],
                    "content": row["content"],
                    "context": json.loads(row["context_json"]) if row["context_json"] else {},
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                results.append(entry)
            
            # Cache results
            result_data = {
                "success": True,
                "results": results,
                "total": len(results),
                "query": query,
                "filters": filters
            }
            
            expires_at = int(time.time()) + CACHE_DURATION
            conn.execute("""
                INSERT OR REPLACE INTO search_cache (query_hash, query_data, result_data, timestamp, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query_hash, json.dumps(query_data), json.dumps(result_data), int(time.time()), expires_at))
            conn.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("search", True, duration_ms)
        
        debug_log(f"Search completed: {len(results)} results")
        return result_data
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("search", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"Search failed: {e}")

def list_entries(params: Dict[str, Any]) -> Dict[str, Any]:
    """List recent history entries with optional filtering."""
    start_time = time.time()
    
    try:
        filters = params.get("filters", {})
        limit = min(filters.get("limit", 50), MAX_SEARCH_RESULTS)
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            sql = """
                SELECT h.*, GROUP_CONCAT(t.tag) as tags
                FROM history h
                LEFT JOIN tags t ON h.id = t.history_id
                WHERE 1=1
            """
            params_list = []
            
            # Apply filters
            if filters.get("type"):
                sql += " AND h.type = ?"
                params_list.append(filters["type"])
            
            if filters.get("start_time"):
                try:
                    start_ts = int(datetime.fromisoformat(filters["start_time"]).timestamp())
                    sql += " AND h.timestamp >= ?"
                    params_list.append(start_ts)
                except ValueError:
                    raise ValidationError("Invalid start_time format")
            
            if filters.get("end_time"):
                try:
                    end_ts = int(datetime.fromisoformat(filters["end_time"]).timestamp())
                    sql += " AND h.timestamp <= ?"
                    params_list.append(end_ts)
                except ValueError:
                    raise ValidationError("Invalid end_time format")
            
            sql += " GROUP BY h.id ORDER BY h.timestamp DESC LIMIT ?"
            params_list.append(limit)
            
            cursor = conn.execute(sql, params_list)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                entry = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "type": row["type"],
                    "content": row["content"],
                    "context": json.loads(row["context_json"]) if row["context_json"] else {},
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                results.append(entry)
        
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("list", True, duration_ms)
        
        debug_log(f"Listed {len(results)} entries")
        
        return {
            "success": True,
            "results": results,
            "total": len(results),
            "filters": filters
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("list", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"List operation failed: {e}")

def get_stats() -> Dict[str, Any]:
    """Get comprehensive statistics about the history database."""
    start_time = time.time()
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Basic counts
            total_entries = conn.execute("SELECT COUNT(*) as count FROM history").fetchone()["count"]
            total_tags = conn.execute("SELECT COUNT(DISTINCT tag) as count FROM tags").fetchone()["count"]
            
            # Entry types
            type_stats = conn.execute("""
                SELECT type, COUNT(*) as count 
                FROM history 
                GROUP BY type 
                ORDER BY count DESC
            """).fetchall()
            
            # Recent activity (last 24 hours)
            yesterday = int(time.time()) - 86400
            recent_entries = conn.execute("""
                SELECT COUNT(*) as count 
                FROM history 
                WHERE timestamp >= ?
            """, (yesterday,)).fetchone()["count"]
            
            # Top tags
            top_tags = conn.execute("""
                SELECT tag, COUNT(*) as count 
                FROM tags 
                GROUP BY tag 
                ORDER BY count DESC 
                LIMIT 10
            """).fetchall()
            
            # Operation statistics
            op_stats = conn.execute("""
                SELECT operation, 
                       COUNT(*) as total,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                       AVG(duration_ms) as avg_duration_ms
                FROM stats 
                GROUP BY operation
            """).fetchall()
            
            # Database size
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
            
            # Oldest and newest entries
            oldest = conn.execute("SELECT MIN(timestamp) as ts FROM history").fetchone()["ts"]
            newest = conn.execute("SELECT MAX(timestamp) as ts FROM history").fetchone()["ts"]
            
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("stats", True, duration_ms)
        
        return {
            "success": True,
            "stats": {
                "total_entries": total_entries,
                "total_tags": total_tags,
                "recent_entries_24h": recent_entries,
                "database_size_bytes": db_size,
                "oldest_entry": oldest,
                "newest_entry": newest,
                "entry_types": [{"type": row["type"], "count": row["count"]} for row in type_stats],
                "top_tags": [{"tag": row["tag"], "count": row["count"]} for row in top_tags],
                "operations": [
                    {
                        "operation": row["operation"],
                        "total": row["total"],
                        "successful": row["successful"],
                        "success_rate": round(row["successful"] / row["total"] * 100, 2) if row["total"] > 0 else 0,
                        "avg_duration_ms": round(row["avg_duration_ms"], 2) if row["avg_duration_ms"] else 0
                    } for row in op_stats
                ]
            }
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("stats", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"Stats operation failed: {e}")

def export_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Export history data in specified format."""
    start_time = time.time()
    
    try:
        export_format = params.get("format", "json")
        filters = params.get("filters", {})
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            sql = """
                SELECT h.*, GROUP_CONCAT(t.tag) as tags
                FROM history h
                LEFT JOIN tags t ON h.id = t.history_id
                WHERE 1=1
            """
            params_list = []
            
            # Apply filters
            if filters.get("type"):
                sql += " AND h.type = ?"
                params_list.append(filters["type"])
            
            if filters.get("start_time"):
                try:
                    start_ts = int(datetime.fromisoformat(filters["start_time"]).timestamp())
                    sql += " AND h.timestamp >= ?"
                    params_list.append(start_ts)
                except ValueError:
                    raise ValidationError("Invalid start_time format")
            
            if filters.get("end_time"):
                try:
                    end_ts = int(datetime.fromisoformat(filters["end_time"]).timestamp())
                    sql += " AND h.timestamp <= ?"
                    params_list.append(end_ts)
                except ValueError:
                    raise ValidationError("Invalid end_time format")
            
            sql += " GROUP BY h.id ORDER BY h.timestamp DESC"
            
            cursor = conn.execute(sql, params_list)
            rows = cursor.fetchall()
            
            # Format data
            data = []
            for row in rows:
                entry = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "datetime": datetime.fromtimestamp(row["timestamp"]).isoformat(),
                    "type": row["type"],
                    "content": row["content"],
                    "context": json.loads(row["context_json"]) if row["context_json"] else {},
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                data.append(entry)
        
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_export_{timestamp}.{export_format}"
        export_path = DATA_DIR / filename
        
        # Write export file
        if export_format == "json":
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif export_format == "csv":
            import csv
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    for row in data:
                        # Flatten complex fields for CSV
                        csv_row = row.copy()
                        csv_row["context"] = json.dumps(csv_row["context"])
                        csv_row["tags"] = ",".join(csv_row["tags"])
                        writer.writerow(csv_row)
        
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("export", True, duration_ms)
        
        debug_log(f"Exported {len(data)} entries to {export_path}")
        
        return {
            "success": True,
            "exported_count": len(data),
            "export_path": str(export_path),
            "format": export_format,
            "filters": filters
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("export", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"Export operation failed: {e}")

def cleanup_old_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up old history data based on retention policy."""
    start_time = time.time()
    
    try:
        days = params.get("days", DEFAULT_RETENTION_DAYS)
        cutoff_time = int(time.time()) - (days * 86400)
        
        with sqlite3.connect(DB_PATH) as conn:
            # Count entries to be deleted
            count_result = conn.execute(
                "SELECT COUNT(*) as count FROM history WHERE timestamp < ?",
                (cutoff_time,)
            ).fetchone()
            entries_to_delete = count_result["count"]
            
            if entries_to_delete > 0:
                # Delete old entries (cascade will handle tags)
                conn.execute("DELETE FROM history WHERE timestamp < ?", (cutoff_time,))
                
                # Clean up old cache entries
                conn.execute("DELETE FROM search_cache WHERE expires_at < ?", (int(time.time()),))
                
                # Clean up old stats (keep last 30 days)
                stats_cutoff = int(time.time()) - (30 * 86400)
                conn.execute("DELETE FROM stats WHERE timestamp < ?", (stats_cutoff,))
                
                conn.commit()
                
                # Vacuum database to reclaim space
                conn.execute("VACUUM")
        
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("cleanup", True, duration_ms)
        
        debug_log(f"Cleanup completed: removed {entries_to_delete} entries older than {days} days")
        
        return {
            "success": True,
            "entries_deleted": entries_to_delete,
            "retention_days": days,
            "cutoff_timestamp": cutoff_time
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("cleanup", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"Cleanup operation failed: {e}")

def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check of the history system."""
    start_time = time.time()
    
    try:
        health_status = {"success": True, "checks": []}
        
        # Check database connectivity
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT 1").fetchone()
            health_status["checks"].append({
                "name": "database_connectivity",
                "status": "ok",
                "message": "Database connection successful"
            })
        except Exception as e:
            health_status["success"] = False
            health_status["checks"].append({
                "name": "database_connectivity",
                "status": "error",
                "message": f"Database connection failed: {e}"
            })
        
        # Check table integrity
        try:
            with sqlite3.connect(DB_PATH) as conn:
                tables = ["history", "tags", "stats", "search_cache", "history_fts"]
                for table in tables:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    if result is not None:
                        continue
            health_status["checks"].append({
                "name": "table_integrity",
                "status": "ok",
                "message": "All required tables exist and accessible"
            })
        except Exception as e:
            health_status["success"] = False
            health_status["checks"].append({
                "name": "table_integrity",
                "status": "error",
                "message": f"Table integrity check failed: {e}"
            })
        
        # Check disk space
        try:
            import shutil
            disk_usage = shutil.disk_usage(DATA_DIR)
            free_space_mb = disk_usage.free // (1024 * 1024)
            
            if free_space_mb < 100:  # Less than 100MB
                health_status["success"] = False
                health_status["checks"].append({
                    "name": "disk_space",
                    "status": "warning",
                    "message": f"Low disk space: {free_space_mb}MB free"
                })
            else:
                health_status["checks"].append({
                    "name": "disk_space",
                    "status": "ok",
                    "message": f"Sufficient disk space: {free_space_mb}MB free"
                })
        except Exception as e:
            health_status["checks"].append({
                "name": "disk_space",
                "status": "warning",
                "message": f"Could not check disk space: {e}"
            })
        
        # Check database size and performance
        try:
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
            db_size_mb = db_size // (1024 * 1024)
            
            with sqlite3.connect(DB_PATH) as conn:
                # Quick performance test
                perf_start = time.time()
                conn.execute("SELECT COUNT(*) FROM history").fetchone()
                perf_duration = (time.time() - perf_start) * 1000
                
                health_status["checks"].append({
                    "name": "database_performance",
                    "status": "ok" if perf_duration < 1000 else "warning",
                    "message": f"DB size: {db_size_mb}MB, Query time: {perf_duration:.2f}ms"
                })
        except Exception as e:
            health_status["success"] = False
            health_status["checks"].append({
                "name": "database_performance",
                "status": "error",
                "message": f"Performance check failed: {e}"
            })
        
        # Check FTS index
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT * FROM history_fts LIMIT 1").fetchone()
            health_status["checks"].append({
                "name": "fts_index",
                "status": "ok",
                "message": "Full-text search index is functional"
            })
        except Exception as e:
            health_status["success"] = False
            health_status["checks"].append({
                "name": "fts_index",
                "status": "error",
                "message": f"FTS index check failed: {e}"
            })
        
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("health", health_status["success"], duration_ms)
        
        debug_log(f"Health check completed: {'OK' if health_status['success'] else 'ISSUES FOUND'}")
        
        return health_status
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        record_operation("health", False, duration_ms, error_type=type(e).__name__)
        raise HistoryError(f"Health check failed: {e}")

def main():
    """Main entry point with comprehensive error handling."""
    try:
        # Initialize database first
        init_database()
        
        if len(sys.argv) < 2:
            print(json.dumps({
                "error": "Parameters required. Usage: python history_tool.py '<json_parameters>'",
                "success": False
            }))
            sys.exit(1)
        
        # Parse parameters
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error": f"Invalid JSON parameters: {e}",
                "success": False
            }))
            sys.exit(1)
        
        # Validate parameters
        validated_params = validate_parameters(params)
        operation = validated_params["operation"]
        
        debug_log(f"Executing operation: {operation}")
        
        # Route to appropriate operation
        if operation == "add":
            result = add_entry(validated_params)
        elif operation == "search":
            result = search_entries(validated_params)
        elif operation == "list":
            result = list_entries(validated_params)
        elif operation == "stats":
            result = get_stats()
        elif operation == "export":
            result = export_data(validated_params)
        elif operation == "cleanup":
            result = cleanup_old_data(validated_params)
        elif operation == "health":
            result = health_check()
        else:
            result = {
                "error": f"Unknown operation: {operation}",
                "success": False
            }
        
        # Output result as JSON
        print(json.dumps(result, ensure_ascii=False))
        
    except ValidationError as e:
        print(json.dumps({
            "error": f"Validation error: {e}",
            "success": False,
            "error_type": "validation"
        }))
        sys.exit(1)
    except DatabaseError as e:
        print(json.dumps({
            "error": f"Database error: {e}",
            "success": False,
            "error_type": "database"
        }))
        sys.exit(1)
    except HistoryError as e:
        print(json.dumps({
            "error": str(e),
            "success": False,
            "error_type": "history"
        }))
        sys.exit(1)
    except Exception as e:
        debug_log(f"Fatal error: {e}", "ERROR")
        print(json.dumps({
            "error": f"Internal error: {e}",
            "success": False,
            "error_type": "internal"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
