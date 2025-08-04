import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_voice_stream_multilingual():
    # This is a placeholder for a real test.
    # A more comprehensive test would involve sending audio data
    # and verifying the transcribed and synthesized output.
    with client.websocket_connect("/voice/stream/test_user?language=es&voice=es_ES-sharvard-medium") as websocket:
        assert websocket.scope["query_string"] == b"language=es&voice=es_ES-sharvard-medium"
