from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.voice_pipeline import VoicePipeline
from ...services.live_agent import LiveAgentService

router = APIRouter(prefix="/voice", tags=["voice"])
voice_pipeline = VoicePipeline()
agent_service = LiveAgentService()

@router.websocket("/stream/{user_id}")
async def voice_stream(websocket: WebSocket, user_id: str):
    await websocket.accept()
    
    try:
        async def audio_stream():
            while True:
                data = await websocket.receive_bytes()
                # Convert bytes to audio samples
                audio_samples = np.frombuffer(data, dtype=np.int16)
                yield audio_samples
        
        # Process voice stream
        async for transcript in voice_pipeline.transcribe_streaming(audio_stream()):
            # Get agent response
            response = await agent_service.process_message(user_id, transcript)
            
            # Stream back audio response
            async for audio_chunk in voice_pipeline.synthesize_streaming(response['response']):
                await websocket.send_bytes(audio_chunk)
                
    except WebSocketDisconnect:
        print(f"Voice connection closed for user {user_id}")