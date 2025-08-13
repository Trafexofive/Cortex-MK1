#!/usr/bin/env python3
"""
StorageUnitMk1 - Universal Key-Value Storage for Agents
Clean, minimal storage system with atomic operations and TTL support.
"""

import json
import os
import sys
import time
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List



# Configuration
# DATA_DIR = Path(os.getenv("AGENT_WORKSPACE", ".")) / ".data"
# store in ./.data relative to the script
DATA_DIR = Path(__file__).resolve().parent.parent / ".data"

DB_PATH = DATA_DIR / "storage_unit_mk1.db"

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def init_database():
    """Initialize SQLite database with storage schema."""
    ensure_data_dir()
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS storage (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER,
                PRIMARY KEY (namespace, key)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                operation TEXT,
                namespace TEXT,
                timestamp INTEGER,
                success BOOLEAN
            )
        ''')
        
        conn.execute('CREATE INDEX IF NOT EXISTS idx_expires ON storage(expires_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_stats_time ON stats(timestamp)')
        conn.commit()

def log_operation(operation: str, namespace: str, success: bool):
    """Log operation for statistics."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                'INSERT INTO stats (operation, namespace, timestamp, success) VALUES (?, ?, ?, ?)',
                (operation, namespace, int(time.time()), success)
            )
            conn.commit()
    except:
        pass  # Silent fail for logging

def cleanup_expired():
    """Remove expired entries."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            now = int(time.time())
            conn.execute('DELETE FROM storage WHERE expires_at IS NOT NULL AND expires_at < ?', (now,))
            conn.commit()
    except:
        pass

def validate_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize parameters."""
    operation = params.get("operation", "").strip()
    if not operation:
        raise ValueError("Operation is required")
    
    namespace = params.get("namespace", "default").strip()
    if not namespace or not namespace.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Invalid namespace format")
    
    validated = {
        "operation": operation,
        "namespace": namespace
    }
    
    if operation in ["store", "retrieve", "delete"]:
        key = params.get("key", "").strip()
        if not key:
            raise ValueError(f"Key is required for {operation} operation")
        validated["key"] = key
    
    if operation == "store":
        value = params.get("value")
        if value is None:
            raise ValueError("Value is required for store operation")
        validated["value"] = str(value)
        
        ttl = params.get("ttl")
        if ttl is not None:
            try:
                ttl = int(ttl)
                if ttl > 0:
                    validated["expires_at"] = int(time.time()) + ttl
            except (ValueError, TypeError):
                raise ValueError("TTL must be a positive integer")
    
    if operation == "list":
        pattern = params.get("pattern", "").strip()
        validated["pattern"] = pattern
    
    return validated

def store_value(namespace: str, key: str, value: str, expires_at: Optional[int] = None) -> Dict[str, Any]:
    """Store a key-value pair."""
    cleanup_expired()
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT OR REPLACE INTO storage (namespace, key, value, created_at, expires_at) VALUES (?, ?, ?, ?, ?)',
            (namespace, key, value, int(time.time()), expires_at)
        )
        conn.commit()
    
    return {
        "success": True,
        "message": f"Stored {key} in {namespace}",
        "namespace": namespace,
        "key": key,
        "expires_at": expires_at
    }

def retrieve_value(namespace: str, key: str) -> Dict[str, Any]:
    """Retrieve a value by key."""
    cleanup_expired()
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            'SELECT value, created_at, expires_at FROM storage WHERE namespace = ? AND key = ?',
            (namespace, key)
        )
        row = cursor.fetchone()
    
    if not row:
        return {
            "success": False,
            "error": f"Key '{key}' not found in namespace '{namespace}'"
        }
    
    value, created_at, expires_at = row
    
    return {
        "success": True,
        "namespace": namespace,
        "key": key,
        "value": value,
        "created_at": created_at,
        "expires_at": expires_at
    }

def delete_value(namespace: str, key: str) -> Dict[str, Any]:
    """Delete a key-value pair."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            'DELETE FROM storage WHERE namespace = ? AND key = ?',
            (namespace, key)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return {
                "success": False,
                "error": f"Key '{key}' not found in namespace '{namespace}'"
            }
    
    return {
        "success": True,
        "message": f"Deleted {key} from {namespace}",
        "namespace": namespace,
        "key": key
    }

def list_keys(namespace: str, pattern: str = "") -> Dict[str, Any]:
    """List keys in a namespace, optionally filtered by pattern."""
    cleanup_expired()
    
    with sqlite3.connect(DB_PATH) as conn:
        if pattern:
            # Simple wildcard support
            sql_pattern = pattern.replace("*", "%").replace("?", "_")
            cursor = conn.execute(
                'SELECT key, created_at, expires_at FROM storage WHERE namespace = ? AND key LIKE ? ORDER BY key',
                (namespace, sql_pattern)
            )
        else:
            cursor = conn.execute(
                'SELECT key, created_at, expires_at FROM storage WHERE namespace = ? ORDER BY key',
                (namespace,)
            )
        
        keys = []
        for row in cursor.fetchall():
            key, created_at, expires_at = row
            keys.append({
                "key": key,
                "created_at": created_at,
                "expires_at": expires_at
            })
    
    return {
        "success": True,
        "namespace": namespace,
        "pattern": pattern,
        "keys": keys,
        "count": len(keys)
    }

def get_stats() -> Dict[str, Any]:
    """Get storage statistics."""
    cleanup_expired()
    
    with sqlite3.connect(DB_PATH) as conn:
        # Storage stats
        storage_cursor = conn.execute(
            'SELECT namespace, COUNT(*) as count FROM storage GROUP BY namespace'
        )
        namespaces = dict(storage_cursor.fetchall())
        
        total_cursor = conn.execute('SELECT COUNT(*) FROM storage')
        total_keys = total_cursor.fetchone()[0]
        
        # Operation stats (last 24 hours)
        day_ago = int(time.time()) - 86400
        ops_cursor = conn.execute(
            'SELECT operation, COUNT(*) as count FROM stats WHERE timestamp > ? GROUP BY operation',
            (day_ago,)
        )
        operations = dict(ops_cursor.fetchall())
    
    return {
        "success": True,
        "total_keys": total_keys,
        "namespaces": namespaces,
        "operations_24h": operations,
        "database_size": DB_PATH.stat().st_size if DB_PATH.exists() else 0
    }

def clear_namespace(namespace: str) -> Dict[str, Any]:
    """Clear all data in a namespace."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('DELETE FROM storage WHERE namespace = ?', (namespace,))
        conn.commit()
        deleted_count = cursor.rowcount
    
    return {
        "success": True,
        "message": f"Cleared {deleted_count} keys from {namespace}",
        "namespace": namespace,
        "deleted_count": deleted_count
    }

def backup_data() -> Dict[str, Any]:
    """Create a backup of all storage data."""
    backup_file = DATA_DIR / f"storage_backup_{int(time.time())}.json"
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT namespace, key, value, created_at, expires_at FROM storage')
        data = []
        for row in cursor.fetchall():
            data.append({
                "namespace": row[0],
                "key": row[1],
                "value": row[2],
                "created_at": row[3],
                "expires_at": row[4]
            })
    
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "message": f"Backup created with {len(data)} entries",
        "backup_file": str(backup_file),
        "entry_count": len(data)
    }

def main():
    """Main entry point."""
    try:
        init_database()
        
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Parameters required", "success": False}))
            sys.exit(1)
        
        params = json.loads(sys.argv[1])
        validated_params = validate_params(params)
        
        operation = validated_params["operation"]
        namespace = validated_params["namespace"]
        
        # Route operations
        if operation == "store":
            result = store_value(
                namespace, 
                validated_params["key"], 
                validated_params["value"],
                validated_params.get("expires_at")
            )
        elif operation == "retrieve":
            result = retrieve_value(namespace, validated_params["key"])
        elif operation == "delete":
            result = delete_value(namespace, validated_params["key"])
        elif operation == "list":
            result = list_keys(namespace, validated_params.get("pattern", ""))
        elif operation == "stats":
            result = get_stats()
        elif operation == "clear":
            result = clear_namespace(namespace)
        elif operation == "backup":
            result = backup_data()
        else:
            result = {"error": f"Unknown operation: {operation}", "success": False}
        
        # Log operation
        log_operation(operation, namespace, result.get("success", False))
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": str(e), "success": False}))
        sys.exit(1)

if __name__ == "__main__":
    main()
