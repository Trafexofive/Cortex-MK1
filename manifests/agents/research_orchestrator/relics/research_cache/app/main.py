"""
Research Cache Relic - Vector Store with TTL and Cleanup
FastAPI-based cache service with automated cleanup workflows
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Research Cache", version="1.0")

# Database setup
DB_PATH = Path("/data/research_cache.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            ttl INTEGER DEFAULT 3600,
            accessed_at INTEGER NOT NULL,
            access_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Models
class CacheItem(BaseModel):
    key: str
    value: Dict[str, Any]
    ttl: Optional[int] = 3600  # Default 1 hour

class CacheResponse(BaseModel):
    success: bool
    key: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class StatsResponse(BaseModel):
    total_entries: int
    expired_entries: int
    total_size_bytes: int
    oldest_entry: Optional[str] = None
    newest_entry: Optional[str] = None

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "research_cache",
        "version": "1.0",
        "timestamp": int(time.time())
    }

@app.post("/store")
async def store_item(item: CacheItem) -> CacheResponse:
    """Store item in cache with TTL"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = int(time.time())
        value_json = json.dumps(item.value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, created_at, ttl, accessed_at, access_count)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (item.key, value_json, now, item.ttl, now))
        
        conn.commit()
        conn.close()
        
        return CacheResponse(
            success=True,
            key=item.key,
            message="Item stored successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get/{key}")
async def get_item(key: str) -> CacheResponse:
    """Retrieve item from cache"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value, created_at, ttl, access_count
            FROM cache
            WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Key not found")
        
        value_json, created_at, ttl, access_count = row
        now = int(time.time())
        
        # Check if expired
        if ttl > 0 and (now - created_at) > ttl:
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            raise HTTPException(status_code=404, detail="Key expired")
        
        # Update access stats
        cursor.execute("""
            UPDATE cache
            SET accessed_at = ?, access_count = ?
            WHERE key = ?
        """, (now, access_count + 1, key))
        
        conn.commit()
        conn.close()
        
        return CacheResponse(
            success=True,
            key=key,
            value=json.loads(value_json)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/{key}")
async def delete_item(key: str) -> CacheResponse:
    """Delete item from cache"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if affected == 0:
            raise HTTPException(status_code=404, detail="Key not found")
        
        return CacheResponse(
            success=True,
            key=key,
            message="Item deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup")
async def cleanup_expired() -> CacheResponse:
    """Remove expired entries (called by cleanup workflow)"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = int(time.time())
        
        cursor.execute("""
            DELETE FROM cache
            WHERE ttl > 0 AND (? - created_at) > ttl
        """, (now,))
        
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return CacheResponse(
            success=True,
            message=f"Cleaned up {deleted} expired entries"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats() -> StatsResponse:
    """Get cache statistics"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = int(time.time())
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM cache")
        total = cursor.fetchone()[0]
        
        # Expired entries
        cursor.execute("""
            SELECT COUNT(*) FROM cache
            WHERE ttl > 0 AND (? - created_at) > ttl
        """, (now,))
        expired = cursor.fetchone()[0]
        
        # Total size (approximate)
        cursor.execute("SELECT SUM(LENGTH(value)) FROM cache")
        size = cursor.fetchone()[0] or 0
        
        # Oldest and newest
        cursor.execute("SELECT key FROM cache ORDER BY created_at ASC LIMIT 1")
        oldest_row = cursor.fetchone()
        oldest = oldest_row[0] if oldest_row else None
        
        cursor.execute("SELECT key FROM cache ORDER BY created_at DESC LIMIT 1")
        newest_row = cursor.fetchone()
        newest = newest_row[0] if newest_row else None
        
        conn.close()
        
        return StatsResponse(
            total_entries=total,
            expired_entries=expired,
            total_size_bytes=size,
            oldest_entry=oldest,
            newest_entry=newest
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_cache(query: str, limit: int = 10) -> Dict[str, Any]:
    """Simple search in cache keys"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, value FROM cache
            WHERE key LIKE ?
            LIMIT ?
        """, (f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "key": row[0],
                "value": json.loads(row[1])
            })
        
        conn.close()
        
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
