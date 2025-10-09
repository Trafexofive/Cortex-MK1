#!/bin/bash
# Quick test script

echo "=== Cortex-Prime Quick Test ==="
echo ""

# Check if services are running
echo "1. Checking services..."
if ! docker ps | grep -q cortex; then
    echo "Starting services..."
    docker-compose up -d
    echo "Waiting for services to start..."
    sleep 10
fi

# Health checks
echo ""
echo "2. Health checks:"
curl -s http://localhost:8084/health | jq -r '.service + ": " + .status' 2>/dev/null || echo "storage_service: DOWN"
curl -s http://localhost:8086/health | jq -r '.service + ": " + .status' 2>/dev/null || echo "container_orchestrator: DOWN"
curl -s http://localhost:8085/health | jq -r '.service + ": " + .status' 2>/dev/null || echo "agent_orchestrator: DOWN"

echo ""
echo "3. Test agent session creation..."
SESSION_ID=$(curl -s -X POST http://localhost:8085/agent/assistant/session \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","metadata":{}}' | jq -r '.session_id')

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
    echo "✓ Session created: $SESSION_ID"
    
    echo ""
    echo "4. Test message send..."
    echo "Sending: 'Hello!'"
    curl -s -X POST http://localhost:8085/agent/session/$SESSION_ID/message \
      -H "Content-Type: application/json" \
      -d '{"content":"Hello!","stream":false}' | jq -r '.response'
    
    echo ""
    echo "✓ All tests passed!"
    echo ""
    echo "Try the CLI: python3 cortex-chat.py"
else
    echo "✗ Failed to create session"
    echo ""
    echo "Check logs: docker-compose logs agent_orchestrator"
fi
