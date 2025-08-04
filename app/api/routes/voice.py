from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ...core.voice_pipeline import VoicePipeline
from ...services.live_agent import LiveAgentService
import numpy as np

router = APIRouter(prefix="/voice", tags=["voice"])
agent_service = LiveAgentService()

@router.websocket("/stream/{user_id}")
async def voice_stream(websocket: WebSocket, user_id: str, language: str = Query("en"), voice: str = Query("en_US-lessac-medium")):
    await websocket.accept()
    voice_pipeline = VoicePipeline(language=language, piper_voice=voice)

    try:
        async def audio_stream():
            while True:
                data = await websocket.receive_bytes()
                # Convert bytes to audio samples
                audio_samples = np.frombuffer(data, dtype=np.int16)
                yield audio_samples

        # Process voice stream
        async for transcript in voice_pipeline.transcribe_streaming(audio_stream(), language=language):
            # Get agent response
            response = await agent_service.process_message(user_id, transcript)

            # Stream back audio response
            async for audio_chunk in voice_pipeline.synthesize_streaming(response['response'], voice=voice):
                await websocket.send_bytes(audio_chunk)

    except WebSocketDisconnect:
        print(f"Voice connection closed for user {user_id}")
