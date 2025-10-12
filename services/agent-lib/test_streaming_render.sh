#!/bin/bash
# Test streaming rendering with demurge agent

cd "$(dirname "$0")"

echo "Testing streaming protocol rendering improvements..."
echo ""
echo "Loading Demurge and asking for multi-thought response..."
echo ""

./agent-bin -l config/agents/demurge/agent.yml <<'EOF'
Create a Python function that calculates fibonacci numbers. Use multiple <thought> blocks to show your design process, and make sure to send at least one non-final response with final="false".
/quit
EOF

echo ""
echo "Test complete. Check if:"
echo "1. Thoughts appear smoothly without character-by-character jitter"
echo "2. Response text appears in the correct location"
echo "3. No text appears outside of proper tags"
echo "4. Action markers appear at the right time"
