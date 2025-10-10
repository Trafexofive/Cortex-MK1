#!/bin/bash
# Quick Start Guide - Using Cortex Agent System NOW

echo "🚀 Cortex-Prime MK1 - Quick Start"
echo "=================================="
echo ""

# Check if services are running
echo "1️⃣  Checking services..."
docker-compose ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null | grep -v WARN

echo ""
echo "2️⃣  Creating a test session..."

# Create session
SESSION=$(curl -s -X POST http://localhost:8085/agent/research_orchestrator/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "quickstart_user"}' | jq -r '.session_id')

if [ "$SESSION" = "null" ] || [ -z "$SESSION" ]; then
    echo "❌ Failed to create session. Is the service running?"
    echo ""
    echo "Start services with: docker-compose up -d"
    exit 1
fi

echo "✅ Session created: $SESSION"
echo ""

echo "3️⃣  Sending a test message..."
echo ""

# Send a simple message
curl -s -X POST "http://localhost:8085/agent/session/${SESSION}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello! What can you help me with?",
    "stream": false
  }' | jq '.'

echo ""
echo "=================================="
echo "✅ Quick test complete!"
echo ""
echo "📚 Usage Examples:"
echo ""
echo "# Create a new session"
echo "SESSION=\$(curl -s -X POST http://localhost:8085/agent/research_orchestrator/session \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"user_id\": \"your_id\"}' | jq -r '.session_id')"
echo ""
echo "# Send a message"
echo "curl -X POST \"http://localhost:8085/agent/session/\${SESSION}/message\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"content\": \"Your message here\", \"stream\": false}' | jq '.'"
echo ""
echo "# List all sessions"
echo "curl -s http://localhost:8085/agent/sessions | jq '.'"
echo ""
echo "# Check service health"
echo "curl -s http://localhost:8085/health | jq '.'"
echo ""
echo "📖 See INTEGRATION_DONE.md for more details"
