from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...services.live_agent import LiveAgentService

router = APIRouter(prefix="/agent", tags=["agent"])
agent_service = LiveAgentService()

@router.websocket("/stream/{user_id}")
async def agent_stream(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            response = await agent_service.process_message(user_id, message)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        print(f"Agent connection closed for user {user_id}")
