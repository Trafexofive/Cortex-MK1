"""
==============================================================================
SESSION MANAGER V2 - Runtime Executor Integration
==============================================================================
Simplified session manager that routes to Runtime Executor for streaming
protocol execution.
==============================================================================
"""

import httpx
import json
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from loguru import logger

from models.orchestrator_models import (
    SessionCreateRequest,
    SessionInfo,
    MessageRequest,
    StreamChunk,
    SessionStatus
)


# Streaming Protocol System Prompt
STREAMING_PROTOCOL_INSTRUCTIONS = """
You MUST respond using Streaming Protocol v1.1 format:

<thought>
Your reasoning here. You can embed actions while thinking:
<action type="tool" mode="async" id="unique_id">
{
  "name": "tool_name",
  "parameters": {"param": "value"},
  "output_key": "variable_name"
}
</action>
Continue thinking while actions run...
</thought>

<response final="true">
Your final answer to the user.
</response>

RULES:
- Use <thought> for reasoning (visible to user)
- Embed <action> in thoughts to start execution early
- Actions with mode="async" run in parallel
- Actions with mode="sync" block until complete
- Use depends_on=["id1","id2"] for dependencies
- Reference action outputs with $variable_name
- Set final="false" for partial responses, final="true" when done
- Action types: tool, agent, relic, workflow, llm, internal

EXAMPLE:
<thought>
I need to fetch data from two sources.
<action type="tool" mode="async" id="fetch1">
{"name": "web_scraper", "parameters": {"url": "https://example.com"}, "output_key": "data1"}
</action>
<action type="tool" mode="async" id="fetch2">
{"name": "api_call", "parameters": {"endpoint": "/data"}, "output_key": "data2"}
</action>
While those run, I'll plan the analysis.
</thought>

<action type="agent" mode="sync" id="analyze" depends_on=["fetch1","fetch2"]>
{"name": "analyzer", "parameters": {"input1": "$data1", "input2": "$data2"}}
</action>

<response final="true">
Analysis complete: ...
</response>
"""


class SessionManager:
    """Manages agent sessions with Runtime Executor integration."""
    
    def __init__(
        self,
        storage_url: str,
        llm_url: str,
        manifest_url: str,
        container_url: str,
        runtime_url: str
    ):
        self.storage_url = storage_url.rstrip('/')
        self.llm_url = llm_url.rstrip('/')
        self.manifest_url = manifest_url.rstrip('/')
        self.container_url = container_url.rstrip('/')
        self.runtime_url = runtime_url.rstrip('/')
        
        self.client = httpx.AsyncClient(timeout=120.0)
        
        logger.info("🎭 Session manager v2 initialized with Runtime Executor")
    
    async def create_session(self, request: SessionCreateRequest) -> SessionInfo:
        """Create a new agent session."""
        
        # 1. Fetch agent manifest
        manifest = await self._fetch_manifest("Agent", request.agent_name)
        if not manifest:
            raise ValueError(f"Agent not found: {request.agent_name}")
        
        # 2. Create session in storage
        session_response = await self.client.post(
            f"{self.storage_url}/storage/sessions",
            json={
                "agent_name": request.agent_name,
                "user_id": request.user_id,
                "metadata": request.metadata
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["id"]
        
        # 3. Initialize state if provided
        if request.initial_state:
            await self.client.put(
                f"{self.storage_url}/storage/state/{session_id}",
                json={"data": request.initial_state}
            )
        
        logger.info(f"✅ Created session {session_id} for agent {request.agent_name}")
        
        return SessionInfo(
            session_id=session_id,
            agent_name=request.agent_name,
            user_id=request.user_id,
            status=SessionStatus.ACTIVE,
            created_at=datetime.fromisoformat(session_data["created_at"]),
            updated_at=datetime.fromisoformat(session_data["updated_at"]),
            message_count=0,
            active_relics=[]
        )
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session info."""
        try:
            response = await self.client.get(f"{self.storage_url}/storage/sessions/{session_id}")
            response.raise_for_status()
            session_data = response.json()
            
            # Count messages
            history_response = await self.client.get(
                f"{self.storage_url}/storage/history",
                params={"session_id": session_id}
            )
            message_count = len(history_response.json()) if history_response.status_code == 200 else 0
            
            return SessionInfo(
                session_id=session_data["id"],
                agent_name=session_data["agent_name"],
                user_id=session_data.get("user_id"),
                status=SessionStatus(session_data["status"]),
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"]),
                message_count=message_count,
                active_relics=[]
            )
        except httpx.HTTPStatusError:
            return None
    
    async def end_session(self, session_id: str) -> bool:
        """End a session."""
        await self.client.put(
            f"{self.storage_url}/storage/sessions/{session_id}",
            json={"status": "ended"}
        )
        logger.info(f"🛑 Ended session {session_id}")
        return True
    
    async def send_message(
        self,
        session_id: str,
        request: MessageRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Send message to agent via Runtime Executor."""
        
        try:
            # 1. Get session
            session = await self.get_session(session_id)
            if not session:
                yield StreamChunk(type="error", data={"error": f"Session not found: {session_id}"})
                return
            
            # 2. Load conversation history
            history = await self._load_history(session_id)
            
            # 3. Save user message
            await self.client.post(
                f"{self.storage_url}/storage/history",
                json={
                    "session_id": session_id,
                    "role": "user",
                    "content": request.content,
                    "metadata": request.metadata
                }
            )
            
            # 4. Build messages with streaming protocol instructions
            messages = [
                {"role": "system", "content": STREAMING_PROTOCOL_INSTRUCTIONS}
            ] + history + [
                {"role": "user", "content": request.content}
            ]
            
            # 5. Call LLM to get streaming protocol response
            llm_response = await self.client.post(
                f"{self.llm_url}/completion",
                json={
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False
                }
            )
            llm_response.raise_for_status()
            llm_data = llm_response.json()
            protocol_text = llm_data.get("content", "")
            
            logger.debug(f"LLM returned protocol: {protocol_text[:200]}...")
            
            # 6. Send protocol to Runtime Executor for parsing and execution
            async with self.client.stream(
                "POST",
                f"{self.runtime_url}/execute/streaming_protocol",
                json={
                    "protocol_text": protocol_text,
                    "session_id": session_id
                }
            ) as runtime_response:
                async for line in runtime_response.aiter_lines():
                    if line.startswith("data: "):
                        event_data = json.loads(line[6:])
                        
                        # Forward events to user
                        event_type = event_data.get("token_type", "unknown")
                        content = event_data.get("content", "")
                        
                        if event_type == "thought":
                            yield StreamChunk(type="thought", data=content)
                        elif event_type == "action":
                            yield StreamChunk(type="action", data=event_data)
                        elif event_type == "response":
                            yield StreamChunk(type="content", data=content)
            
            # 7. Save assistant response
            await self.client.post(
                f"{self.storage_url}/storage/history",
                json={
                    "session_id": session_id,
                    "role": "assistant",
                    "content": protocol_text,
                    "metadata": {}
                }
            )
            
            yield StreamChunk(type="done", data={"message": "Complete"})
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            yield StreamChunk(type="error", data={"error": str(e)})
    
    async def _fetch_manifest(self, kind: str, name: str) -> Optional[Dict[str, Any]]:
        """Fetch manifest from manifest_ingestion."""
        try:
            response = await self.client.get(
                f"{self.manifest_url}/registry/manifest/{kind}/{name}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch manifest {kind}/{name}: {e}")
            return None
    
    async def _load_history(self, session_id: str) -> list:
        """Load conversation history."""
        try:
            response = await self.client.get(
                f"{self.storage_url}/storage/history",
                params={"session_id": session_id, "limit": 50}
            )
            response.raise_for_status()
            messages = response.json()
            
            return [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]
        except Exception:
            return []
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
