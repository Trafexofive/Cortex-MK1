# Cortex-Prime - Quick Start

## Run Everything

```bash
# 1. Set API keys
export GEMINI_API_KEY=your_key_here

# 2. Start all services
docker-compose up -d

# 3. Wait for services (30s)
sleep 30

# 4. Test
./test.sh

# 5. Chat
python3 cortex-chat.py
```

## CLI Commands

```bash
# Chat with default agent
python3 cortex-chat.py

# Chat with specific agent
python3 cortex-chat.py research_orchestrator

# In chat:
/quit - Exit
/new - New session
```

## Check Services

```bash
# All services
docker-compose ps

# Logs
docker-compose logs -f agent_orchestrator

# Stop
docker-compose down
```

## Direct API Test

```bash
# Create session
SESSION_ID=$(curl -s -X POST http://localhost:8085/agent/assistant/session \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","metadata":{}}' | jq -r '.session_id')

# Send message
curl -X POST http://localhost:8085/agent/session/$SESSION_ID/message \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello!","stream":false}' | jq -r '.response'
```

## Troubleshooting

**Services won't start**:
```bash
docker-compose logs
```

**Can't connect**:
```bash
curl http://localhost:8085/health
```

**No LLM response**:
- Check GEMINI_API_KEY is set
- Check llm_gateway logs: `docker-compose logs llm_gateway`
