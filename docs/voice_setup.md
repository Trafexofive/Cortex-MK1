# Voice Setup

## 🎤 Voice Pipeline

### Ultra-Fast Voice Service (app/core/voice_pipeline.py)

The voice pipeline is designed for ultra-low latency, featuring a streaming architecture that processes audio in small chunks. It uses `whisper.cpp` for transcription and `Piper TTS` for synthesis, both of which are highly optimized for speed.

### WebSocket Voice Handler (app/api/routes/voice.py)

The WebSocket handler manages the real-time, bidirectional communication for the voice stream. It receives audio data from the client, passes it to the voice pipeline for processing, and streams the synthesized audio response back to the client.
