"""
Fact Store Relic - Simple Key-Value Storage
FastAPI-based storage service for default-worker-agent
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sqlite3
import json
from pathlib import Path
import time

app = FastAPI(title="Fact Store", version="1.0")

# Database setup
DB_PATH = Path("/data/fact_store.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Models
class Fact(BaseModel):
    key: str
    value: Dict[str, Any]

class FactResponse(BaseModel):
    success: bool
    key: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fact_store",
        "version": "1.0",
        "timestamp": int(time.time())
    }

@app.get("/system/capabilities")
async def get_capabilities():
    """Return service capabilities"""
    return {
        "service": "fact_store",
        "version": "1.0",
        "operations": [
            {
                "name": "set_fact",
                "method": "POST",
                "endpoint": "/set",
                "description": "Store a fact"
            },
            {
                "name": "get_fact",
                "method": "GET",
                "endpoint": "/get/{key}",
                "description": "Retrieve a fact"
            },
            {
                "name": "delete_fact",
                "method": "DELETE",
                "endpoint": "/delete/{key}",
                "description": "Delete a fact"
            }
        ]
    }

@app.post("/set")
async def set_fact(fact: Fact) -> FactResponse:
    """Store a fact"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = int(time.time())
        value_json = json.dumps(fact.value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO facts (key, value, created_at, updated_at)
            VALUES (?, ?, COALESCE((SELECT created_at FROM facts WHERE key = ?), ?), ?)
        """, (fact.key, value_json, fact.key, now, now))
        
        conn.commit()
        conn.close()
        
        return FactResponse(
            success=True,
            key=fact.key,
            message="Fact stored successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get/{key}")
async def get_fact(key: str) -> FactResponse:
    """Retrieve a fact"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM facts WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Fact not found")
        
        return FactResponse(
            success=True,
            key=key,
            value=json.loads(row[0])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/{key}")
async def delete_fact(key: str) -> FactResponse:
    """Delete a fact"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM facts WHERE key = ?", (key,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if affected == 0:
            raise HTTPException(status_code=404, detail="Fact not found")
        
        return FactResponse(
            success=True,
            key=key,
            message="Fact deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/keys")
async def list_keys() -> Dict[str, Any]:
    """List all fact keys"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, created_at, updated_at FROM facts")
        rows = cursor.fetchall()
        
        conn.close()
        
        keys = [
            {
                "key": row[0],
                "created_at": row[1],
                "updated_at": row[2]
            }
            for row in rows
        ]
        
        return {
            "success": True,
            "count": len(keys),
            "keys": keys
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get storage statistics"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM facts")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(LENGTH(value)) FROM facts")
        size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "success": True,
            "total_facts": total,
            "total_size_bytes": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
