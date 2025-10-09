"""
==============================================================================
SESSION MANAGER - Agent Session Orchestration
==============================================================================
Coordinates agent sessions, message routing, and context injection.
==============================================================================
"""

import httpx
import json
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
from loguru import logger

from models.orchestrator_models import (
    SessionCreateRequest,
    SessionInfo,
    MessageRequest,
    MessageResponse,
    ToolCall,
    ToolResult,
    StreamChunk,
    SessionStatus,
    MessageRole
)


class SessionManager:
    """Manages agent session orchestration."""
    
    def __init__(
        self,
        storage_url: str,
        llm_url: str,
        manifest_url: str,
        container_url: str
    ):
        self.storage_url = storage_url.rstrip('/')
        self.llm_url = llm_url.rstrip('/')
        self.manifest_url = manifest_url.rstrip('/')
        self.container_url = container_url.rstrip('/')
        
        self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.info("🎭 Session manager initialized")
    
    # ========================================================================
    # SESSION LIFECYCLE
    # ========================================================================
    
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
        
        # 3. Initialize state
        if request.initial_state:
            await self.client.put(
                f"{self.storage_url}/storage/state/{session_id}",
                json={"data": request.initial_state}
            )
        
        # 4. Start required relics (if any)
        active_relics = []
        relics = manifest.get("import", {}).get("relics", [])
        for relic_path in relics:
            # Extract relic name from path
            relic_name = relic_path.split("/")[-1].replace(".yml", "").replace("relic.", "")
            
            try:
                # Fetch relic manifest
                relic_manifest = await self._fetch_manifest("Relic", relic_name)
                if relic_manifest:
                    # Start relic via container orchestrator
                    relic_info = await self._start_relic(session_id, relic_name, relic_manifest)
                    active_relics.append(relic_name)
            except Exception as e:
                logger.warning(f"Failed to start relic {relic_name}: {e}")
        
        logger.info(f"✅ Created session {session_id} for agent {request.agent_name}")
        
        return SessionInfo(
            session_id=session_id,
            agent_name=request.agent_name,
            user_id=request.user_id,
            status=SessionStatus.ACTIVE,
            created_at=datetime.fromisoformat(session_data["created_at"]),
            updated_at=datetime.fromisoformat(session_data["updated_at"]),
            message_count=0,
            active_relics=active_relics
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
                active_relics=[]  # TODO: Track relics
            )
        except httpx.HTTPStatusError:
            return None
    
    async def end_session(self, session_id: str) -> bool:
        """End a session and cleanup resources."""
        
        # 1. Update session status
        await self.client.put(
            f"{self.storage_url}/storage/sessions/{session_id}",
            json={"status": "ended"}
        )
        
        # 2. Cleanup containers (relics)
        try:
            await self.client.post(
                f"{self.container_url}/containers/cleanup/session",
                json={"session_id": session_id, "force": True}
            )
        except Exception as e:
            logger.warning(f"Failed to cleanup containers for session {session_id}: {e}")
        
        logger.info(f"🛑 Ended session {session_id}")
        return True
    
    # ========================================================================
    # MESSAGE HANDLING
    # ========================================================================
    
    async def send_message(
        self,
        session_id: str,
        request: MessageRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Send message to agent and stream response."""
        
        try:
            # 1. Get session info
            session = await self.get_session(session_id)
            if not session:
                yield StreamChunk(type="error", data={"error": f"Session not found: {session_id}"})
                return
            
            # 2. Fetch agent manifest
            manifest = await self._fetch_manifest("Agent", session.agent_name)
            
            # 3. Load conversation history
            history = await self._load_history(session_id)
            
            # 4. Load agent state
            state = await self._load_state(session_id)
            
            # 5. Build context (system prompt + tools + relics)
            context = await self._build_context(manifest, state)
            
            # 6. Add user message to history
            await self.client.post(
                f"{self.storage_url}/storage/history",
                json={
                    "session_id": session_id,
                    "role": "user",
                    "content": request.content,
                    "metadata": request.metadata
                }
            )
            
            # 7. Send to LLM and stream response with agentic loop
            messages = context["messages"] + history + [{"role": "user", "content": request.content}]
            
            # Agentic loop - continue until LLM stops calling tools
            max_iterations = 10
            iteration = 0
            final_response = ""
            
            while iteration < max_iterations:
                iteration += 1
                logger.debug(f"Agentic loop iteration {iteration}")
                
                # Get LLM response with streaming
                assistant_message = ""
                tool_calls = []
                
                async for chunk in self._stream_llm_completion(messages, context.get("tools", [])):
                    if chunk["type"] == "content":
                        assistant_message += chunk["data"]
                        yield StreamChunk(type="content", data=chunk["data"])
                    elif chunk["type"] == "tool_call":
                        tool_calls.append(chunk["data"])
                        yield StreamChunk(type="tool_call", data=chunk["data"])
                
                # 8. Handle tool calls if any
                if tool_calls:
                    # Add assistant message with tool calls to conversation
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message or None,
                        "tool_calls": tool_calls
                    })
                    
                    # Execute each tool and add results
                    for tool_call in tool_calls:
                        # Execute tool
                        tool_result = await self._execute_tool(session_id, tool_call)
                        yield StreamChunk(type="tool_result", data=tool_result.dict())
                        
                        # Add tool result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "name": tool_call["name"],
                            "content": json.dumps(tool_result.result) if tool_result.result else tool_result.error or "No result"
                        })
                    
                    # Continue loop to get LLM's next response with tool results
                    continue
                else:
                    # No tool calls - we're done
                    final_response = assistant_message
                    
                    # 9. Save final assistant message
                    await self.client.post(
                        f"{self.storage_url}/storage/history",
                        json={
                            "session_id": session_id,
                            "role": "assistant",
                            "content": final_response,
                            "metadata": {}
                        }
                    )
                    break
            
            # 10. Update state if needed
            # (Could extract state updates from LLM response)
            
            yield StreamChunk(type="done", data={"message": final_response})
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            yield StreamChunk(type="error", data={"error": str(e)})
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
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
    
    async def _load_history(self, session_id: str) -> List[Dict[str, str]]:
        """Load conversation history from storage."""
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
    
    async def _load_state(self, session_id: str) -> Dict[str, Any]:
        """Load agent state from storage."""
        try:
            response = await self.client.get(f"{self.storage_url}/storage/state/{session_id}")
            if response.status_code == 200:
                return response.json().get("data", {})
        except Exception:
            pass
        return {}
    
    async def _build_context(self, manifest: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Build LLM context from manifest and state."""
        
        # 1. Load system prompt/persona
        system_prompt = await self._load_persona(manifest)
        
        # 2. Load tools with proper schemas
        tools = await self._load_tool_schemas(manifest)
        
        # 3. Build initial messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # 4. Add state to system message if present
        if state:
            messages[0]["content"] += f"\n\nCurrent state: {json.dumps(state)}"
        
        # 5. Build context
        context = {
            "messages": messages,
            "tools": tools if tools else None
        }
        
        return context
    
    async def _load_persona(self, manifest: Dict[str, Any]) -> str:
        """Load persona/system prompt from manifest."""
        # Try to get system_prompt from manifest
        system_prompt = manifest.get("system_prompt")
        if system_prompt:
            return system_prompt
        
        # Try to load from persona file
        persona_path = manifest.get("persona", {}).get("agent")
        if persona_path:
            # For now, use a generic prompt (could be enhanced to load from file)
            return f"You are {manifest.get('name', 'an AI assistant')}. {manifest.get('description', '')}"
        
        return "You are a helpful AI assistant."
    
    async def _load_tool_schemas(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load tool schemas from manifests."""
        tools = []
        
        for tool_path in manifest.get("import", {}).get("tools", []):
            # Extract tool name from path (e.g., "tools/google_search/tool.yml" -> "google_search")
            path_parts = tool_path.split("/")
            if len(path_parts) >= 2:
                tool_name = path_parts[-2]  # Get directory name before the file
            else:
                tool_name = tool_path.split("/")[-1].replace(".yml", "").replace("tool.", "")
            
            logger.info(f"Loading tool schema for: {tool_name} (from {tool_path})")
            
            # Fetch tool manifest
            tool_manifest = await self._fetch_manifest("Tool", tool_name)
            if not tool_manifest:
                logger.warning(f"Tool manifest not found: {tool_name}")
                continue
            
            # Build tool schema
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_manifest.get("description", f"Tool {tool_name}"),
                    "parameters": await self._build_tool_parameters(tool_manifest)
                }
            }
            tools.append(tool_schema)
        
        return tools
    
    async def _build_tool_parameters(self, tool_manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Build tool parameter schema from manifest."""
        # Try to get input schema (new format)
        input_schema = tool_manifest.get("input", {})
        
        # If we have a proper schema, use it
        if "properties" in input_schema:
            return {
                "type": "object",
                "properties": input_schema.get("properties", {}),
                "required": input_schema.get("required", [])
            }
        
        # Try parameters format (legacy format)
        parameters = tool_manifest.get("parameters", [])
        if parameters:
            properties = {}
            required = []
            
            for param in parameters:
                param_name = param.get("name")
                if param_name:
                    properties[param_name] = {
                        "type": param.get("type", "string"),
                        "description": param.get("description", "")
                    }
                    if param.get("required", False):
                        required.append(param_name)
            
            return {
                "type": "object",
                "properties": properties,
                "required": required
            }
        
        # Fallback to empty object
        return {"type": "object", "properties": {}}
    
    async def _stream_llm_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream completion from LLM gateway."""
        
        request_data = {
            "messages": messages,
            "model": "gemini-1.5-flash",
            "stream": False  # Use non-streaming for now to get tool_calls properly
        }
        
        if tools:
            request_data["tools"] = tools
        
        logger.debug(f"🔧 Sending {len(tools) if tools else 0} tools to LLM")
        logger.debug(f"🔧 Tools: {json.dumps(tools) if tools else 'None'}")
        
        try:
            response = await self.client.post(
                f"{self.llm_url}/completion",
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle tool calls
            if data.get("tool_calls"):
                for tc in data["tool_calls"]:
                    yield {"type": "tool_call", "data": {
                        "id": tc.get("id"),
                        "name": tc.get("function", {}).get("name"),
                        "arguments": json.loads(tc.get("function", {}).get("arguments", "{}"))
                    }}
            
            # Handle content
            if data.get("content"):
                yield {"type": "content", "data": data["content"]}
                
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            yield {"type": "error", "data": str(e)}
    
    async def _execute_tool(self, session_id: str, tool_call: Dict[str, Any]) -> ToolResult:
        """Execute a tool via container orchestrator."""
        
        tool_name = tool_call["name"]
        arguments = tool_call.get("arguments", {})
        
        try:
            # Execute tool in container
            response = await self.client.post(
                f"{self.container_url}/containers/tool/execute",
                json={
                    "tool_name": tool_name,
                    "session_id": session_id,
                    "parameters": arguments,
                    "image": f"cortex/tool-{tool_name}:latest",
                    "cleanup": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult(
                call_id=tool_call.get("id", "unknown"),
                name=tool_name,
                result=result.get("result", result.get("stdout")),
                error=result.get("error")
            )
        except Exception as e:
            return ToolResult(
                call_id=tool_call.get("id", "unknown"),
                name=tool_name,
                result=None,
                error=str(e)
            )
    
    async def _start_relic(
        self,
        session_id: str,
        relic_name: str,
        manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start a relic container."""
        
        response = await self.client.post(
            f"{self.container_url}/containers/relic/start",
            json={
                "relic_name": relic_name,
                "session_id": session_id,
                "image": f"cortex/relic-{relic_name}:latest",
                "create_private_network": True,
                "health_check_endpoint": "/health"
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
