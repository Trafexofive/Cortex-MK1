"""Message handling API routes."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from models.orchestrator_models import MessageRequest
import json

router = APIRouter(prefix="/agent/session", tags=["messages"])


@router.post("/{session_id}/message")
async def send_message(session_id: str, request_data: MessageRequest, req: Request):
    """Send message to agent and stream response."""
    session_manager = req.app.state.session_manager
    
    if request_data.stream:
        # Streaming response
        async def generate():
            async for chunk in session_manager.send_message(session_id, request_data):
                # Send as SSE
                yield f"data: {json.dumps(chunk.dict())}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Non-streaming response (collect all chunks)
        chunks = []
        async for chunk in session_manager.send_message(session_id, request_data):
            chunks.append(chunk)
        
        # Return final message
        content_chunks = [c.data for c in chunks if c.type == "content"]
        content = "".join(content_chunks) if content_chunks else ""
        
        return {
            "session_id": session_id,
            "response": content,
            "chunks": [c.dict() for c in chunks]
        }
