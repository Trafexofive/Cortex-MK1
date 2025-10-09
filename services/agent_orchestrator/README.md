# Agent Orchestrator

**"The Conductor" - Agent session coordination for Cortex-Prime**

Port: 8085

## Overview

The Agent Orchestrator coordinates all agent interactions, managing sessions, routing messages, injecting context, and executing tools/relics through other services.

## Features

- **Session Management**: Create, track, and end agent sessions
- **Message Routing**: Route user messages to LLM with context
- **Context Injection**: System prompts, tools, relics, state
- **Tool Execution**: Execute tools via container_orchestrator
- **Relic Management**: Start relics for sessions
- **State Persistence**: Save conversation history and agent state
- **Streaming Responses**: Server-sent events for real-time updates

## Architecture

```
agent_orchestrator/
├── main.py                     # FastAPI application
├── models/
│   └── orchestrator_models.py  # Pydantic models
├── managers/
│   └── session_manager.py      # Session coordination
├── api/
│   ├── sessions.py             # Session endpoints
│   └── messages.py             # Message endpoints
├── Dockerfile
├── requirements.txt
└── README.md
```

## API Endpoints

### Sessions
```bash
POST   /agent/{agent_name}/session     # Create session
GET    /agent/session/{id}             # Get session info
DELETE /agent/session/{id}             # End session
GET    /agent/session/{id}/history     # Get history
GET    /agent/session/{id}/state       # Get state
```

### Messages
```bash
POST   /agent/session/{id}/message     # Send message (streaming)
```

## Usage

### Create Session
```bash
curl -X POST http://localhost:8085/agent/research_orchestrator/session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "initial_state": {},
    "metadata": {"source": "cli"}
  }'
```

### Send Message (Streaming)
```bash
curl -X POST http://localhost:8085/agent/session/{session_id}/message \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is quantum computing?",
    "stream": true
  }' \
  --no-buffer
```

## How It Works

### Session Creation Flow
1. Client requests session for agent
2. Fetch agent manifest from manifest_ingestion
3. Create session in storage_service
4. Initialize agent state
5. Start required relics via container_orchestrator
6. Return session info

### Message Flow
1. Client sends message
2. Load session, manifest, history, state from storage
3. Build LLM context (system prompt, tools, relics)
4. Add user message to history
5. Stream to LLM gateway
6. Parse response (content or tool calls)
7. Execute tools via container_orchestrator if needed
8. Save assistant message and state
9. Stream response to client

## Dependencies

- **storage_service** (8084): Session/history/state persistence
- **llm_gateway** (8081): LLM inference
- **manifest_ingestion** (8082): Agent/tool/relic manifests
- **container_orchestrator** (8086): Tool/relic execution

## Environment Variables

- `HOST`: Host to bind (default: 0.0.0.0)
- `PORT`: Port (default: 8085)
- `STORAGE_URL`: Storage service URL
- `LLM_URL`: LLM gateway URL
- `MANIFEST_URL`: Manifest ingestion URL
- `CONTAINER_URL`: Container orchestrator URL

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Or with Docker
docker build -t cortex/agent-orchestrator .
docker run -p 8085:8085 cortex/agent-orchestrator
```

## License

Part of Cortex-Prime MK1 ecosystem.
