#!/usr/bin/env python3
import json
import os
import sys
import uuid
from pathlib import Path
import sqlite3

# Define the data directory and database path
DATA_DIR = Path(os.getenv("AGENT_WORKSPACE", ".")) / ".data"
DB_PATH = DATA_DIR / "artifacts.db"

def ensure_data_dir():
    """Create the data directory if it doesn’t exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def init_database():
    """Ensure the artifacts table exists in the database."""
    ensure_data_dir()
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT
            )
        """)
        conn.commit()

def create_artifact(data):
    """Create a new artifact and return its ID."""
    artifact_id = str(uuid.uuid4())
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO artifacts (id, content, metadata) VALUES (?, ?, ?)",
            (artifact_id, json.dumps(data), json.dumps({}))
        )
        conn.commit()
    return artifact_id

def read_artifact(artifact_id):
    """Retrieve an artifact by ID."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content, metadata FROM artifacts WHERE id = ?", (artifact_id,))
        row = cursor.fetchone()
        if row:
            content = json.loads(row[0])
            metadata = json.loads(row[1])
            return {"id": artifact_id, "content": content, "metadata": metadata}
    return None

def update_artifact(artifact_id, data):
    """Update an existing artifact’s content."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE artifacts SET content = ? WHERE id = ?",
            (json.dumps(data), artifact_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_artifact(artifact_id):
    """Delete an artifact by ID."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
        conn.commit()
        return cursor.rowcount > 0

def list_artifacts():
    """List all artifact IDs."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM artifacts")
        rows = cursor.fetchall()
        return [row[0] for row in rows]

def main():
    init_database()  # Ensure the database and table exist

    if len(sys.argv) < 2:
        print("Error: Operation type required.", file=sys.stderr)
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON parameters: {e}", file=sys.stderr)
        sys.exit(1)

    operation = params.get("operation")
    if not operation:
        print("Error: 'operation' parameter missing.", file=sys.stderr)
        sys.exit(1)

    if operation == "create":
        data = params.get("data")
        if data is None:
            print("Error: 'data' required for create operation.", file=sys.stderr)
            sys.exit(1)
        artifact_id = create_artifact(data)
        print(json.dumps({"artifact_id": artifact_id, "success": True}))

    elif operation == "read":
        artifact_id = params.get("artifact_id")
        if not artifact_id:
            print("Error: 'artifact_id' required for read operation.", file=sys.stderr)
            sys.exit(1)
        artifact = read_artifact(artifact_id)
        if artifact:
            print(json.dumps(artifact))
        else:
            print(json.dumps({"error": "Artifact not found", "success": False}))

    elif operation == "update":
        artifact_id = params.get("artifact_id")
        data = params.get("data")
        if not artifact_id or data is None:
            print("Error: 'artifact_id' and 'data' required for update operation.", file=sys.stderr)
            sys.exit(1)
        success = update_artifact(artifact_id, data)
        print(json.dumps({"success": success}))

    elif operation == "delete":
        artifact_id = params.get("artifact_id")
        if not artifact_id:
            print("Error: 'artifact_id' required for delete operation.", file=sys.stderr)
            sys.exit(1)
        success = delete_artifact(artifact_id)
        print(json.dumps({"success": success}))

    elif operation == "list":
        artifacts = list_artifacts()
        print(json.dumps({"artifacts": artifacts, "success": True}))

    else:
        print(f"Error: Unknown operation '{operation}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
