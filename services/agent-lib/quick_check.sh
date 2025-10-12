#!/bin/bash
# Quick test of agent-lib functionality
# Run this anytime to verify agent-lib is working

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║         AGENT-LIB QUICK FUNCTIONALITY CHECK              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Binary exists
if [ -x "./agent-bin" ]; then
    echo "✅ agent-bin binary exists and is executable"
else
    echo "❌ agent-bin binary not found - run 'make bin'"
    exit 1
fi

# Test 2: Sage manifest loads
echo "✅ Testing Sage agent loading..."
cat > /tmp/quick-test.txt <<'EOF'
/load config/agents/sage/agent.yml
/quit
EOF

if ./agent-bin < /tmp/quick-test.txt 2>&1 | grep -q "Successfully loaded"; then
    echo "✅ Sage agent loads correctly"
else
    echo "❌ Sage agent failed to load"
fi

# Test 3: Demurge manifest loads
echo "✅ Testing Demurge agent loading..."
cat > /tmp/quick-test.txt <<'EOF'
/load config/agents/demurge/agent.yml
/quit
EOF

if ./agent-bin < /tmp/quick-test.txt 2>&1 | grep -q "Successfully loaded"; then
    echo "✅ Demurge agent loads correctly"
else
    echo "❌ Demurge agent failed to load"
fi

# Test 4: Tool execution
echo "✅ Testing tool execution..."
if python3 config/agents/sage/tools/knowledge_retriever/scripts/knowledge_retriever.py \
   '{"query": "test", "depth": "quick"}' 2>&1 | grep -q "success"; then
    echo "✅ Tools execute correctly"
else
    echo "❌ Tool execution failed"
fi

rm -f /tmp/quick-test.txt

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              QUICK CHECK COMPLETE                        ║"
echo "║                                                          ║"
echo "║  For comprehensive testing, run:                         ║"
echo "║  ./test_agent_lib.sh                                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
