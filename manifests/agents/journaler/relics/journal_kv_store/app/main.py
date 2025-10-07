import sqlite3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import os

# --- Configuration ---
DB_PATH = os.getenv("SQLITE_DB_PATH", "/data/journal_kv_store.db")

app = FastAPI(
    title="Journal KV Store Relic",
    description="A simple, persistent key-value storage service for the journaler agent.",
    version="1.0.0"
)

# --- Database Setup ---
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS kv_store (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        conn.commit()

@app.on_event("startup")
def on_startup():
    init_db()

# --- Pydantic Models ---
class SetRequest(BaseModel):
    key: str
    value: Any

# --- API Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/system/capabilities")
def get_capabilities():
    return {
        "relic_name": "journal_kv_store",
        "operations": [
            {"name": "get_value", "description": "Gets the value for a given key."},
            {"name": "set_value", "description": "Sets a value for a given key."},
            {"name": "delete_value", "description": "Deletes a key-value pair."}
        ]
    }

@app.post("/set")
def set_value(item: SetRequest):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
                (item.key, json.dumps(item.value))
            )
            conn.commit()
        return {"success": True, "key": item.key, "value": item.value}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/get/{key}")
def get_value(key: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
            row = cursor.fetchone()
        if row:
            return {"success": True, "key": key, "value": json.loads(row[0])}
        else:
            raise HTTPException(status_code=404, detail="Key not found")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.delete("/delete/{key}")
def delete_value(key: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            conn.commit()
        if cursor.rowcount > 0:
            return {"success": True, "key": key, "message": "Key deleted"}
        else:
            raise HTTPException(status_code=404, detail="Key not found")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
