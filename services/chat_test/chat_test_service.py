"""
==============================================================================
CHAT TEST SERVICE - MVP for Testing Streaming Protocol
==============================================================================
Simple FastAPI service with SSE streaming to test the agent protocol
==============================================================================
"""

import os
import asyncio
import json
from typing import Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import httpx for API calls
import httpx

# Add runtime_executor to path
import sys
from pathlib import Path
runtime_executor_path = Path(__file__).parent / "runtime_executor"
if runtime_executor_path.exists():
    sys.path.insert(0, str(runtime_executor_path))
else:
    # Fallback to parent directory structure
    sys.path.insert(0, str(Path(__file__).parent.parent / "runtime_executor"))

from streaming_protocol_parser import StreamingProtocolParser, ParsedAction


# ============================================================================
# MODELS
# ============================================================================

class ChatMessage(BaseModel):
    message: str
    agent_name: Optional[str] = "test_agent"
    stream: bool = True


# ============================================================================
# MOCK TOOLS FOR TESTING
# ============================================================================

async def execute_tool(name: str, parameters: dict) -> dict:
    """Mock tool execution"""
    await asyncio.sleep(0.5)  # Simulate execution
    
    tool_responses = {
        "web_scraper": {
            "status": "success",
            "data": f"Scraped data from {parameters.get('url', 'unknown')}",
            "content": "Sample webpage content about AI and machine learning..."
        },
        "calculator": {
            "status": "success",
            "result": parameters.get('a', 0) + parameters.get('b', 0)
        },
        "arxiv_search": {
            "status": "success",
            "papers": [
                {"title": "Attention Is All You Need", "authors": "Vaswani et al."},
                {"title": "BERT: Pre-training of Deep Bidirectional Transformers", "authors": "Devlin et al."}
            ]
        },
        "database_query": {
            "status": "success",
            "rows": 42,
            "data": "Sample database results..."
        }
    }
    
    return tool_responses.get(name, {"status": "success", "message": f"Executed {name}"})


async def execute_action(action: ParsedAction) -> dict:
    """Execute an action based on type"""
    print(f"🎬 Executing action: {action.name} (type: {action.type}, mode: {action.mode})")
    
    if action.type == "tool":
        result = await execute_tool(action.name, action.parameters)
    elif action.type == "agent":
        result = {"status": "delegated", "agent": action.name, "result": "Agent completed successfully"}
    elif action.type == "relic":
        result = {"status": "called", "relic": action.name, "result": "Relic operation completed"}
    else:
        result = {"status": "executed", "type": action.type}
    
    print(f"✅ Action completed: {action.name}")
    return result


# ============================================================================
# LLM INTEGRATION
# ============================================================================

async def mock_llm_stream(prompt: str) -> AsyncGenerator[str, None]:
    """Mock LLM streaming for testing"""
    
    response = f"""<thought>
Let me help you with that. I'll demonstrate the streaming protocol by:
1. Showing my thinking process in real-time
2. Executing a few test actions in parallel
3. Providing a comprehensive response
</thought>

<action type="tool" mode="async" id="fetch_wiki">
{{
  "name": "web_scraper",
  "parameters": {{
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
  }},
  "output_key": "wiki_data"
}}
</action>

<action type="tool" mode="async" id="search_papers">
{{
  "name": "arxiv_search",
  "parameters": {{
    "query": "machine learning",
    "max_results": 5
  }},
  "output_key": "papers"
}}
</action>

<action type="tool" mode="sync" id="calc">
{{
  "name": "calculator",
  "parameters": {{
    "a": 42,
    "b": 8
  }},
  "depends_on": [],
  "output_key": "calc_result"
}}
</action>

<response>
# Response to: "{prompt[:50]}..."

I've successfully executed the following actions:

## Data Gathered
- **Wikipedia**: Retrieved AI article
- **arXiv**: Found recent ML papers  
- **Calculation**: 42 + 8 = 50

## Summary
This demonstrates the streaming protocol working in real-time! As you can see:
- My thinking was streamed immediately
- Actions executed in parallel (wiki + arxiv)
- Results are available for reference
- All done while the response was still being generated

**Status**: ✅ All systems operational!
</response>"""
    
    # Stream character by character to simulate LLM
    for char in response:
        yield char
        await asyncio.sleep(0.002)  # Simulate token delay


async def llm_gateway_stream(prompt: str, llm_gateway_url: str = "http://llm_gateway:8080") -> AsyncGenerator[str, None]:
    """Stream from LLM Gateway service"""
    
    # System instruction for the protocol
    system_message = """You are a helpful AI assistant that uses the Cortex streaming protocol.

You MUST structure your responses using this format:

<thought>
Your reasoning and planning
</thought>

<action type="TYPE" mode="MODE" id="ID">
{
  "name": "action_name",
  "parameters": {...},
  "output_key": "var_name"
}
</action>

<response>
Your final answer
</response>

Available tools:
- web_scraper: {"url": "..."}
- calculator: {"a": number, "b": number}
- arxiv_search: {"query": "...", "max_results": number}
- database_query: {"query": "..."}

Use mode="async" for parallel operations, mode="sync" when you need to wait for results.
"""
    
    request_payload = {
        "provider": "gemini",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{llm_gateway_url}/completion",
                json=request_payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "content" in data:
                                yield data["content"]
                            elif "error" in data:
                                print(f"❌ LLM Gateway error: {data['error']}")
                                break
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        print(f"❌ LLM Gateway connection error: {e}")
        print("📝 Falling back to mock LLM")
        # Fallback to mock
        async for char in mock_llm_stream(prompt):
            yield char


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Cortex Chat Test",
    description="Testing interface for streaming protocol",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve chat interface"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Cortex Chat Test</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            width: 100%;
            max-width: 900px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .status {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            gap: 12px;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }
        
        .message.user .message-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .message.agent .message-avatar {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .message-content {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 15px;
            line-height: 1.6;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.agent .message-content {
            background: white;
            color: #1e293b;
            border: 1px solid #e2e8f0;
        }
        
        .thought {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            font-style: italic;
            color: #92400e;
        }
        
        .action {
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
        }
        
        .action-header {
            font-weight: 600;
            color: #1e40af;
            margin-bottom: 5px;
        }
        
        .action-details {
            font-size: 13px;
            color: #475569;
            font-family: 'Courier New', monospace;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e2e8f0;
            display: flex;
            gap: 10px;
        }
        
        .input-container input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e2e8f0;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-container input:focus {
            border-color: #667eea;
        }
        
        .input-container button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .input-container button:hover {
            transform: translateY(-2px);
        }
        
        .input-container button:active {
            transform: translateY(0);
        }
        
        .input-container button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            display: none;
            padding: 15px 20px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            width: fit-content;
        }
        
        .typing-indicator.active {
            display: flex;
            gap: 5px;
            align-items: center;
        }
        
        .dot {
            width: 8px;
            height: 8px;
            background: #94a3b8;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="status"></span>
            <h1>🧠 Cortex Chat Test</h1>
        </div>
        
        <div class="chat-container" id="chat">
            <div class="message agent">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <strong>Welcome to Cortex Chat!</strong><br><br>
                    I'm using the new streaming execution protocol. Watch as I:
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        <li>Stream my thinking in real-time 💭</li>
                        <li>Execute actions in parallel 🔄</li>
                        <li>Provide progressive feedback ⚡</li>
                    </ul>
                    <br>Try asking me to do something!
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typing">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
        
        <div class="input-container">
            <input type="text" id="input" placeholder="Type your message..." />
            <button id="send" onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('send');
        const typing = document.getElementById('typing');
        
        let currentMessage = null;
        let currentThought = null;
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage('user', message);
            input.value = '';
            sendBtn.disabled = true;
            typing.classList.add('active');
            
            try {
                const response = await fetch('/chat/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, stream: true })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                currentMessage = createMessage('agent');
                typing.classList.remove('active');
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.slice(6));
                            handleEvent(data);
                        }
                    }
                }
                
                currentMessage = null;
                currentThought = null;
                
            } catch (error) {
                console.error('Error:', error);
                addMessage('agent', '❌ Error: ' + error.message);
            } finally {
                sendBtn.disabled = false;
                input.focus();
            }
        }
        
        function handleEvent(event) {
            if (event.token_type === 'thought') {
                if (!currentThought) {
                    currentThought = document.createElement('div');
                    currentThought.className = 'thought';
                    currentThought.innerHTML = '<strong>💭 Thinking:</strong> ';
                    currentMessage.appendChild(currentThought);
                }
                currentThought.appendChild(document.createTextNode(event.content));
                scrollToBottom();
            }
            else if (event.token_type === 'action') {
                const action = event.metadata.action;
                const actionDiv = document.createElement('div');
                actionDiv.className = 'action';
                
                const modeEmoji = {
                    'sync': '⏸️',
                    'async': '🔄',
                    'fire_and_forget': '🔥'
                };
                
                actionDiv.innerHTML = `
                    <div class="action-header">
                        ${modeEmoji[action.mode] || '⚙️'} Action: ${action.name}
                    </div>
                    <div class="action-details">
                        Type: ${action.type} | Mode: ${action.mode}
                        ${action.depends_on && action.depends_on.length ? '<br>Depends on: ' + action.depends_on.join(', ') : ''}
                    </div>
                `;
                currentMessage.appendChild(actionDiv);
                scrollToBottom();
            }
            else if (event.token_type === 'response') {
                if (!currentMessage.querySelector('.response')) {
                    const responseDiv = document.createElement('div');
                    responseDiv.className = 'response';
                    responseDiv.innerHTML = '<strong>📝 Response:</strong><br>';
                    currentMessage.appendChild(responseDiv);
                }
                const responseDiv = currentMessage.querySelector('.response');
                responseDiv.appendChild(document.createTextNode(event.content));
                scrollToBottom();
            }
        }
        
        function addMessage(type, content) {
            const msg = document.createElement('div');
            msg.className = `message ${type}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = type === 'user' ? '👤' : '🤖';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            msg.appendChild(avatar);
            msg.appendChild(contentDiv);
            chat.appendChild(msg);
            
            scrollToBottom();
        }
        
        function createMessage(type) {
            const msg = document.createElement('div');
            msg.className = `message ${type}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = type === 'user' ? '👤' : '🤖';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            msg.appendChild(avatar);
            msg.appendChild(contentDiv);
            chat.appendChild(msg);
            
            scrollToBottom();
            return contentDiv;
        }
        
        function scrollToBottom() {
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chat/stream")
async def chat_stream(message: ChatMessage):
    """Stream chat response with protocol parsing"""
    
    async def event_generator():
        # Get LLM Gateway URL from environment
        llm_gateway_url = os.getenv('LLM_GATEWAY_URL', 'http://llm_gateway:8080')
        use_llm_gateway = os.getenv('USE_LLM_GATEWAY', 'true').lower() == 'true'
        
        if use_llm_gateway:
            print(f"🧠 Using LLM Gateway at {llm_gateway_url}")
            llm_stream = llm_gateway_stream(message.message, llm_gateway_url)
        else:
            print("🤖 Using mock LLM")
            llm_stream = mock_llm_stream(message.message)
        
        # Create parser with action executor
        parser = StreamingProtocolParser(action_executor=execute_action)
        
        # Parse and stream events
        async for event in parser.parse_stream(llm_stream):
            event_data = {
                "token_type": event.token_type,
                "content": event.content,
                "metadata": {}
            }
            
            # Add action details if it's an action event
            if event.token_type == "action" and "action" in event.metadata:
                action = event.metadata["action"]
                event_data["metadata"]["action"] = {
                    "id": action.id,
                    "name": action.name,
                    "type": action.type,
                    "mode": action.mode,
                    "depends_on": action.depends_on
                }
            
            yield f"data: {json.dumps(event_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "chat-test"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8888))
    llm_gateway_url = os.getenv('LLM_GATEWAY_URL', 'http://llm_gateway:8080')
    use_llm_gateway = os.getenv('USE_LLM_GATEWAY', 'true').lower() == 'true'
    
    print(f"\n{'='*70}")
    print(f"🚀 Starting Cortex Chat Test Service")
    print(f"{'='*70}")
    print(f"URL: http://localhost:{port}")
    print(f"LLM: {'Gateway (' + llm_gateway_url + ')' if use_llm_gateway else 'Mock'}")
    print(f"{'='*70}\n")
    
    uvicorn.run(
        "chat_test_service:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
