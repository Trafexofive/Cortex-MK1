#!/usr/bin/env python3
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SearchResult(BaseModel):
    file: str
    line: int
    code: str

@app.get("/search", response_model=list[SearchResult])
def search(query: str):
    # Dummy implementation
    return [
        {"file": "src/main.py", "line": 42, "code": "print('Hello, World!')"}
    ]
