from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel
import asyncio
import logging
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Service")

# Use a smaller, faster model for real-time transcription
model_size = "base" 

# This will automatically use CUDA if available.
# The Dockerfile will ensure the environment is set up correctly.
model = WhisperModel(model_size, device="cpu", compute_type="int8")

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to transcription websocket.")
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            audio_file = io.BytesIO(audio_data)
            
            # Transcribe the audio
            segments, info = model.transcribe(audio_file, beam_size=5)
            
            transcription = "".join(segment.text for segment in segments)
            logger.info(f"Transcription: {transcription}")
            
            # Send the transcription back to the client
            await websocket.send_text(transcription)
            
    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error during transcription: {e}", exc_info=True)
        await websocket.close(code=1011)
