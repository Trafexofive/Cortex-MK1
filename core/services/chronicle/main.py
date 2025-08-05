from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI(
    title="Chronicle Service",
    description="A service for storing and retrieving conversation history.",
    version="0.1.0",
)

class HistoryEntry(BaseModel):
    session_id: str
    interaction: dict

# Initialize SQLite database
conn = sqlite3.connect("chronicle.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    interaction TEXT NOT NULL
);
""")
conn.commit()

@app.post("/entries")
async def add_history_entry(entry: HistoryEntry):
    cursor.execute("INSERT INTO history (session_id, interaction) VALUES (?, ?)", 
                   (entry.session_id, str(entry.interaction)))
    conn.commit()
    return {"status": "success"}

@app.post("/search")
async def search_history(session_id: str):
    cursor.execute("SELECT interaction FROM history WHERE session_id = ?", (session_id,))
    rows = cursor.fetchall()
    return {"history": [eval(row[0]) for row in rows]}
