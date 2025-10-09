import sqlite3
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

# Configuration
DB_PATH = os.getenv("SQLITE_DB_PATH", "/data/kv_store.db")

app = FastAPI(
    title="KV Store Relic",
    description="Simple key-value storage service",
    version="1.0.0"
)


# Database initialization
def init_db():
    """Initialize SQLite database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


@app.on_event("startup")
def on_startup():
    """Run on startup"""
    init_db()


# Pydantic models
class SetRequest(BaseModel):
    key: str
    value: Any


# API Endpoints
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "kv_store"}


@app.get("/system/capabilities")
def get_capabilities():
    """Get relic capabilities"""
    return {
        "relic_name": "kv_store",
        "version": "1.0.0",
        "operations": [
            {"name": "set_value", "description": "Store a key-value pair"},
            {"name": "get_value", "description": "Retrieve value by key"},
            {"name": "delete_value", "description": "Delete a key-value pair"}
        ]
    }


@app.post("/set")
def set_value(item: SetRequest):
    """Store a key-value pair"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (item.key, json.dumps(item.value))
            )
            conn.commit()
        return {
            "success": True,
            "key": item.key,
            "message": "Value stored successfully"
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/get/{key}")
def get_value(key: str):
    """Retrieve value by key"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT value, created_at, updated_at FROM kv_store WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "key": key,
                "value": json.loads(row[0]),
                "created_at": row[1],
                "updated_at": row[2]
            }
        else:
            raise HTTPException(status_code=404, detail="Key not found")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.delete("/delete/{key}")
def delete_value(key: str):
    """Delete a key-value pair"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "success": True,
                "key": key,
                "message": "Key deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Key not found")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/list")
def list_keys(limit: int = 100):
    """List all keys"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT key, created_at, updated_at FROM kv_store LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
        
        return {
            "success": True,
            "count": len(rows),
            "keys": [
                {"key": row[0], "created_at": row[1], "updated_at": row[2]}
                for row in rows
            ]
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
