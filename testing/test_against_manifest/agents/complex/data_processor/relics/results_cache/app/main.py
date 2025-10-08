import sqlite3
import json
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

DB_PATH = os.getenv("CACHE_DB_PATH", "/data/results_cache.db")
DEFAULT_TTL = int(os.getenv("DEFAULT_TTL", "3600"))
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "1000"))

app = FastAPI(title="Results Cache Relic", version="1.0.0")


def init_db():
    """Initialize database with TTL support"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        """)
        conn.commit()


@app.on_event("startup")
def on_startup():
    init_db()


class StoreRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = DEFAULT_TTL


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "results_cache"}


@app.post("/store")
def store_result(item: StoreRequest):
    """Store result with TTL"""
    try:
        expires_at = datetime.now() + timedelta(seconds=item.ttl)
        
        with sqlite3.connect(DB_PATH) as conn:
            # Check cache size
            count = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at > datetime('now')").fetchone()[0]
            if count >= MAX_CACHE_SIZE:
                # Remove oldest expired items first
                conn.execute("DELETE FROM cache WHERE expires_at < datetime('now')")
                # If still full, remove oldest items
                count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
                if count >= MAX_CACHE_SIZE:
                    conn.execute("""
                        DELETE FROM cache WHERE key IN (
                            SELECT key FROM cache ORDER BY created_at LIMIT 100
                        )
                    """)
            
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (item.key, json.dumps(item.value), expires_at.isoformat())
            )
            conn.commit()
        
        return {
            "success": True,
            "key": item.key,
            "expires_at": expires_at.isoformat(),
            "ttl": item.ttl
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get/{key}")
def get_result(key: str):
    """Get cached result if not expired"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT value, created_at, expires_at FROM cache
                WHERE key = ? AND expires_at > datetime('now')
            """, (key,))
            row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "key": key,
                "value": json.loads(row[0]),
                "created_at": row[1],
                "expires_at": row[2],
                "cache_hit": True
            }
        else:
            return {
                "success": False,
                "cache_hit": False,
                "message": "Key not found or expired"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats(include_size: bool = False):
    """Get cache statistics"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at > datetime('now')").fetchone()[0]
            expired = total - active
            
            stats = {
                "total_items": total,
                "active_items": active,
                "expired_items": expired,
                "utilization": active / MAX_CACHE_SIZE if MAX_CACHE_SIZE > 0 else 0,
                "max_size": MAX_CACHE_SIZE
            }
            
            if include_size:
                # Calculate approximate size
                cursor = conn.execute("SELECT SUM(LENGTH(value)) FROM cache WHERE expires_at > datetime('now')")
                size_bytes = cursor.fetchone()[0] or 0
                stats["size_bytes"] = size_bytes
                stats["size_mb"] = round(size_bytes / (1024 * 1024), 2)
            
            return {"success": True, **stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/size")
def get_queue_size():
    """Simulate processing queue - returns active cache size"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            count = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at > datetime('now')").fetchone()[0]
        return {"success": True, "queue_size": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recent")
def list_recent(limit: int = 10):
    """List recent cached items"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT key, created_at, expires_at FROM cache
                WHERE expires_at > datetime('now')
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
        
        return {
            "success": True,
            "count": len(rows),
            "items": [
                {
                    "key": row[0],
                    "created_at": row[1],
                    "expires_at": row[2]
                }
                for row in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cleanup")
def cleanup_expired():
    """Manually trigger cleanup of expired items"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE expires_at < datetime('now')")
            conn.commit()
            deleted = cursor.rowcount
        
        return {
            "success": True,
            "deleted_count": deleted,
            "message": f"Cleaned up {deleted} expired items"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
