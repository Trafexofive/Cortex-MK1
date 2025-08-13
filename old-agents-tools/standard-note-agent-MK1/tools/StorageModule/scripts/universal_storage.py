#!/usr/bin/env python3
"""
Universal Storage Module - SQLite-based persistent storage for agents
Provides schema-agnostic data persistence with automatic optimization
"""

import json
import os
import sys
import time
import sqlite3
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
from threading import Lock

# Configuration Constants
DATA_DIR = Path(os.getenv("AGENT_WORKSPACE", ".")) / ".data"
DB_PATH = DATA_DIR / "universal_storage.db"
BACKUP_DIR = DATA_DIR / "backups"
CACHE_DURATION = 300  # 5 minutes
MAX_RETRIES = 3
VACUUM_THRESHOLD = 1000  # Operations before vacuum
PAGE_SIZE = 4096

# Thread safety
db_lock = Lock()

class StorageError(Exception):
    """Base exception for storage-specific errors."""
    pass

class ValidationError(StorageError):
    """Parameter validation errors."""
    pass

class SchemaError(StorageError):
    """Schema-related errors."""
    pass

class QueryError(StorageError):
    """Query execution errors."""
    pass

def ensure_data_dir():
    """Create data directory structure."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def debug_log(message: str, level: str = "INFO"):
    """Centralized logging with levels."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)

@contextmanager
def get_db_connection():
    """Get database connection with proper configuration."""
    with db_lock:
        conn = None
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute(f"PRAGMA page_size = {PAGE_SIZE}")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

def init_database():
    """Initialize database with system tables."""
    ensure_data_dir()
    
    with get_db_connection() as conn:
        # System tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                table_name TEXT,
                timestamp INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                duration_ms INTEGER,
                error_type TEXT,
                row_count INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _table_metadata (
                table_name TEXT PRIMARY KEY,
                schema_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                row_count INTEGER DEFAULT 0,
                auto_increment INTEGER DEFAULT 0
            )
        """)
        
        # Indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_operation ON _system_stats(operation, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_table ON _system_stats(table_name, timestamp)")
        
        conn.commit()

def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize input parameters."""
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    operation = params.get("operation")
    if not operation:
        raise ValidationError("Operation is required")
    
    valid_operations = ["store", "retrieve", "query", "delete", "update", 
                       "create_table", "list_tables", "backup", "restore", 
                       "stats", "health"]
    
    if operation not in valid_operations:
        raise ValidationError(f"Invalid operation: {operation}")
    
    # Validate table name if provided
    table = params.get("table")
    if table and not isinstance(table, str):
        raise ValidationError("Table name must be a string")
    
    if table and not table.replace("_", "").isalnum():
        raise ValidationError("Table name must contain only alphanumeric characters and underscores")
    
    return params

def infer_column_type(value: Any) -> str:
    """Infer SQLite column type from Python value."""
    if isinstance(value, bool):
        return "BOOLEAN"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "REAL"
    elif isinstance(value, (dict, list)):
        return "TEXT"  # Store as JSON
    else:
        return "TEXT"

def create_table_from_data(conn: sqlite3.Connection, table_name: str, data: Dict[str, Any]):
    """Create table with schema inferred from data."""
    columns = []
    for key, value in data.items():
        col_type = infer_column_type(value)
        columns.append(f"{key} {col_type}")
    
    # Add system columns
    columns.extend([
        "_id INTEGER PRIMARY KEY AUTOINCREMENT",
        "_created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))",
        "_updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))"
    ])
    
    create_sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
    conn.execute(create_sql)
    
    # Update metadata
    schema_hash = hashlib.md5(create_sql.encode()).hexdigest()
    now = int(time.time())
    
    conn.execute("""
        INSERT OR REPLACE INTO _table_metadata 
        (table_name, schema_hash, created_at, updated_at) 
        VALUES (?, ?, ?, ?)
    """, (table_name, schema_hash, now, now))

def log_operation(conn: sqlite3.Connection, operation: str, table_name: str, 
                 success: bool, duration_ms: int, error_type: str = None, 
                 row_count: int = None):
    """Log operation statistics."""
    conn.execute("""
        INSERT INTO _system_stats 
        (operation, table_name, timestamp, success, duration_ms, error_type, row_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (operation, table_name, int(time.time()), success, duration_ms, error_type, row_count))

def store_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Store data in specified table."""
    table = params.get("table")
    data = params.get("data")
    
    if not table:
        raise ValidationError("Table name is required for store operation")
    
    if not data or not isinstance(data, dict):
        raise ValidationError("Data must be a non-empty dictionary")
    
    start_time = time.time()
    
    with get_db_connection() as conn:
        try:
            # Check if table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=? AND name NOT LIKE '_system_%'
            """, (table,))
            
            if not cursor.fetchone():
                create_table_from_data(conn, table, data)
            
            # Prepare data for insertion
            insert_data = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    insert_data[key] = json.dumps(value)
                else:
                    insert_data[key] = value
            
            # Insert data
            columns = list(insert_data.keys())
            placeholders = ["?" for _ in columns]
            values = list(insert_data.values())
            
            insert_sql = f"""
                INSERT INTO {table} ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            """
            
            cursor = conn.execute(insert_sql, values)
            row_id = cursor.lastrowid
            
            # Update metadata
            conn.execute("""
                UPDATE _table_metadata 
                SET row_count = row_count + 1, updated_at = ?
                WHERE table_name = ?
            """, (int(time.time()), table))
            
            conn.commit()
            
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "store", table, True, duration_ms, row_count=1)
            
            return {
                "success": True,
                "message": "Data stored successfully",
                "row_id": row_id,
                "table": table
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "store", table, False, duration_ms, str(type(e).__name__))
            raise QueryError(f"Failed to store data: {e}")

def retrieve_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve data by key or all data from table."""
    table = params.get("table")
    key = params.get("key")
    
    if not table:
        raise ValidationError("Table name is required for retrieve operation")
    
    start_time = time.time()
    
    with get_db_connection() as conn:
        try:
            if key:
                # Retrieve specific row by ID
                cursor = conn.execute(f"SELECT * FROM {table} WHERE _id = ?", (key,))
                row = cursor.fetchone()
                
                if row:
                    result_data = dict(row)
                    # Parse JSON fields
                    for k, v in result_data.items():
                        if isinstance(v, str) and v.startswith('{') or v.startswith('['):
                            try:
                                result_data[k] = json.loads(v)
                            except json.JSONDecodeError:
                                pass
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    log_operation(conn, "retrieve", table, True, duration_ms, row_count=1)
                    
                    return {
                        "success": True,
                        "data": result_data,
                        "table": table
                    }
                else:
                    return {
                        "success": False,
                        "message": "Record not found",
                        "table": table
                    }
            else:
                # Retrieve all rows
                cursor = conn.execute(f"SELECT * FROM {table} ORDER BY _created_at DESC")
                rows = cursor.fetchall()
                
                result_data = []
                for row in rows:
                    row_dict = dict(row)
                    # Parse JSON fields
                    for k, v in row_dict.items():
                        if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                            try:
                                row_dict[k] = json.loads(v)
                            except json.JSONDecodeError:
                                pass
                    result_data.append(row_dict)
                
                duration_ms = int((time.time() - start_time) * 1000)
                log_operation(conn, "retrieve", table, True, duration_ms, row_count=len(result_data))
                
                return {
                    "success": True,
                    "data": result_data,
                    "count": len(result_data),
                    "table": table
                }
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "retrieve", table, False, duration_ms, str(type(e).__name__))
            raise QueryError(f"Failed to retrieve data: {e}")

def query_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Query data with filtering and sorting."""
    table = params.get("table")
    query_params = params.get("query", {})
    
    if not table:
        raise ValidationError("Table name is required for query operation")
    
    start_time = time.time()
    
    with get_db_connection() as conn:
        try:
            base_sql = f"SELECT * FROM {table}"
            sql_params = []
            conditions = []
            
            # Build WHERE clause
            where_clause = query_params.get("where", {})
            if where_clause:
                for key, value in where_clause.items():
                    if isinstance(value, (dict, list)):
                        conditions.append(f"{key} = ?")
                        sql_params.append(json.dumps(value))
                    else:
                        conditions.append(f"{key} = ?")
                        sql_params.append(value)
            
            if conditions:
                base_sql += " WHERE " + " AND ".join(conditions)
            
            # Add ORDER BY
            order_by = query_params.get("order_by")
            if order_by:
                base_sql += f" ORDER BY {order_by}"
            else:
                base_sql += " ORDER BY _created_at DESC"
            
            # Add LIMIT and OFFSET
            limit = query_params.get("limit")
            if limit:
                base_sql += f" LIMIT {limit}"
                
                offset = query_params.get("offset")
                if offset:
                    base_sql += f" OFFSET {offset}"
            
            cursor = conn.execute(base_sql, sql_params)
            rows = cursor.fetchall()
            
            result_data = []
            for row in rows:
                row_dict = dict(row)
                # Parse JSON fields
                for k, v in row_dict.items():
                    if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                        try:
                            row_dict[k] = json.loads(v)
                        except json.JSONDecodeError:
                            pass
                result_data.append(row_dict)
            
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "query", table, True, duration_ms, row_count=len(result_data))
            
            return {
                "success": True,
                "data": result_data,
                "count": len(result_data),
                "table": table,
                "query": query_params
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "query", table, False, duration_ms, str(type(e).__name__))
            raise QueryError(f"Failed to query data: {e}")

def update_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Update existing data."""
    table = params.get("table")
    key = params.get("key")
    data = params.get("data")
    
    if not table or not key:
        raise ValidationError("Table name and key are required for update operation")
    
    if not data or not isinstance(data, dict):
        raise ValidationError("Data must be a non-empty dictionary")
    
    start_time = time.time()
    
    with get_db_connection() as conn:
        try:
            # Prepare update data
            update_data = {}
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    update_data[k] = json.dumps(v)
                else:
                    update_data[k] = v
            
            # Add updated timestamp
            update_data["_updated_at"] = int(time.time())
            
            # Build update query
            set_clauses = [f"{k} = ?" for k in update_data.keys()]
            values = list(update_data.values())
            values.append(key)  # For WHERE clause
            
            update_sql = f"""
                UPDATE {table} 
                SET {', '.join(set_clauses)}
                WHERE _id = ?
            """
            
            cursor = conn.execute(update_sql, values)
            
            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "message": "Record not found",
                    "table": table,
                    "key": key
                }
            
            # Update metadata
            conn.execute("""
                UPDATE _table_metadata 
                SET updated_at = ?
                WHERE table_name = ?
            """, (int(time.time()), table))
            
            conn.commit()
            
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "update", table, True, duration_ms, row_count=1)
            
            return {
                "success": True,
                "message": "Data updated successfully",
                "table": table,
                "key": key
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "update", table, False, duration_ms, str(type(e).__name__))
            raise QueryError(f"Failed to update data: {e}")

def delete_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete data by key."""
    table = params.get("table")
    key = params.get("key")
    
    if not table or not key:
        raise ValidationError("Table name and key are required for delete operation")
    
    start_time = time.time()
    
    with get_db_connection() as conn:
        try:
            cursor = conn.execute(f"DELETE FROM {table} WHERE _id = ?", (key,))
            
            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "message": "Record not found",
                    "table": table,
                    "key": key
                }
            
            # Update metadata
            conn.execute("""
                UPDATE _table_metadata 
                SET row_count = row_count - 1, updated_at = ?
                WHERE table_name = ?
            """, (int(time.time()), table))
            
            conn.commit()
            
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "delete", table, True, duration_ms, row_count=1)
            
            return {
                "success": True,
                "message": "Data deleted successfully",
                "table": table,
                "key": key
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_operation(conn, "delete", table, False, duration_ms, str(type(e).__name__))
            raise QueryError(f"Failed to delete data: {e}")

def create_table_explicit(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create table with explicit schema."""
    table = params.get("table")
    schema = params.get("schema")
    
    if not table:
        raise ValidationError("Table name is required for create_table operation")
    
    if not schema or not isinstance(schema, dict):
        raise ValidationError("Schema must be a non-empty dictionary")
    
    with get_db_connection() as conn:
        try:
            columns = []
            for col_name, col_def in schema.items():
                if isinstance(col_def, str):
                    columns.append(f"{col_name} {col_def}")
                elif isinstance(col_def, dict):
                    col_type = col_def.get("type", "TEXT")
                    constraints = col_def.get("constraints", "")
                    columns.append(f"{col_name} {col_type} {constraints}")
            
            # Add system columns
            columns.extend([
                "_id INTEGER PRIMARY KEY AUTOINCREMENT",
                "_created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))",
                "_updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))"
            ])
            
            create_sql = f"CREATE TABLE {table} ({', '.join(columns)})"
            conn.execute(create_sql)
            
            # Update metadata
            schema_hash = hashlib.md5(create_sql.encode()).hexdigest()
            now = int(time.time())
            
            conn.execute("""
                INSERT OR REPLACE INTO _table_metadata 
                (table_name, schema_hash, created_at, updated_at) 
                VALUES (?, ?, ?, ?)
            """, (table, schema_hash, now, now))
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Table '{table}' created successfully",
                "table": table,
                "schema": schema
            }
            
        except Exception as e:
            raise SchemaError(f"Failed to create table: {e}")

def list_tables(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all user tables with metadata."""
    with get_db_connection() as conn:
        try:
            cursor = conn.execute("""
                SELECT 
                    tm.table_name,
                    tm.created_at,
                    tm.updated_at,
                    tm.row_count,
                    COUNT(DISTINCT ss.operation) as operation_count,
                    AVG(ss.duration_ms) as avg_duration_ms
                FROM _table_metadata tm
                LEFT JOIN _system_stats ss ON tm.table_name = ss.table_name
                WHERE tm.table_name NOT LIKE '_system_%'
                GROUP BY tm.table_name
                ORDER BY tm.updated_at DESC
            """)
            
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "name": row["table_name"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "row_count": row["row_count"] or 0,
                    "operation_count": row["operation_count"] or 0,
                    "avg_duration_ms": round(row["avg_duration_ms"] or 0, 2)
                })
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables)
            }
            
        except Exception as e:
            raise QueryError(f"Failed to list tables: {e}")

def backup_database(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create database backup."""
    backup_path = params.get("backup_path")
    
    if not backup_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"storage_backup_{timestamp}.db"
    else:
        backup_path = Path(backup_path)
    
    try:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, backup_path)
        
        return {
            "success": True,
            "message": "Database backup created successfully",
            "backup_path": str(backup_path),
            "size_bytes": backup_path.stat().st_size
        }
        
    except Exception as e:
        raise StorageError(f"Failed to create backup: {e}")

def get_stats(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get usage statistics and performance metrics."""
    with get_db_connection() as conn:
        try:
            # Overall stats
            stats_cursor = conn.execute("""
                SELECT 
                    operation,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success THEN 0 ELSE 1 END) as error_count
                FROM _system_stats 
                WHERE timestamp > (strftime('%s', 'now') - 86400)
                GROUP BY operation
            """)
            
            operation_stats = {}
            for row in stats_cursor.fetchall():
                operation_stats[row["operation"]] = {
                    "count": row["count"],
                    "avg_duration_ms": round(row["avg_duration"] or 0, 2),
                    "success_count": row["success_count"],
                    "error_count": row["error_count"],
                    "success_rate": round((row["success_count"] / row["count"]) * 100, 2)
                }
            
            # Database info
            db_cursor = conn.execute("PRAGMA database_list")
            db_info = db_cursor.fetchone()
            
            size_cursor = conn.execute("PRAGMA page_count")
            page_count = size_cursor.fetchone()[0]
            
            return {
                "success": True,
                "database": {
                    "path": str(DB_PATH),
                    "size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
                    "page_count": page_count,
                    "page_size": PAGE_SIZE
                },
                "operations": operation_stats,
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            raise QueryError(f"Failed to get statistics: {e}")

def health_check(params: Dict[str, Any]) -> Dict[str, Any]:
    """Perform system health check."""
    try:
        start_time = time.time()
        
        with get_db_connection() as conn:
            # Test basic operations
            conn.execute("SELECT 1")
            
            # Check system tables
            tables_cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '_system_%'
            """)
            system_tables = [row[0] for row in tables_cursor.fetchall()]
            
            # Check database integrity
            integrity_cursor = conn.execute("PRAGMA integrity_check")
            integrity_result = integrity_cursor.fetchone()[0]
            
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "status": "healthy",
            "response_time_ms": response_time,
            "database_path": str(DB_PATH),
            "database_exists": DB_PATH.exists(),
            "system_tables": system_tables,
            "integrity_check": integrity_result,
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": int(time.time())
        }

def main():
    """Main entry point with robust error handling."""
    try:
        init_database()
        
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Parameters required", "success": False}))
            sys.exit(1)
        
        params = json.loads(sys.argv[1])
        validated_params = validate_parameters(params)
        
        operation = validated_params.get("operation")
        
        # Operation routing
        if operation == "store":
            result = store_data(validated_params)
        elif operation == "retrieve":
            result = retrieve_data(validated_params)
        elif operation == "query":
            result = query_data(validated_params)
        elif operation == "update":
            result = update_data(validated_params)
        elif operation == "delete":
            result = delete_data(validated_params)
        elif operation == "create_table":
            result = create_table_explicit(validated_params)
        elif operation == "list_tables":
            result = list_tables(validated_params)
        elif operation == "backup":
            result = backup_database(validated_params)
        elif operation == "stats":
            result = get_stats(validated_params)
        elif operation == "health":
            result = health_check(validated_params)
        else:
            result = {"error": f"Unknown operation: {operation}", "success": False}
        
        print(json.dumps(result))
        
    except ValidationError as e:
        debug_log(f"Validation error: {e}", "ERROR")
        print(json.dumps({"error":
