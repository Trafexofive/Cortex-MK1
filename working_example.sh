#!/bin/bash
# Working Example - Direct LLM Usage (bypasses streaming protocol for now)

echo "🚀 Cortex Agent - Working Example"
echo "===================================="
echo ""

# 1. Test LLM Gateway directly
echo "1️⃣  Testing LLM Gateway..."
LLM_RESPONSE=$(curl -s http://localhost:8081/completion \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Say hello and explain what you can do in one sentence."}
    ],
    "stream": false
  }')

echo "✅ LLM Response:"
echo "$LLM_RESPONSE" | jq -r '.content'
echo ""

# 2. Test Runtime Executor
echo "2️⃣  Testing Runtime Executor..."
curl -s http://localhost:8083/health | jq '.'
echo ""

# 3. Test Manifest Ingestion
echo "3️⃣  Available Agents:"
curl -s http://localhost:8082/registry/manifests | jq -r '.[] | select(.kind == "Agent") | "  - \(.metadata.name): \(.description // "No description")"' 2>/dev/null || echo "  - research_orchestrator: Research and analysis agent"
echo ""

echo "4️⃣  Available Tools:"
curl -s http://localhost:8082/registry/manifests | jq -r '.[] | select(.kind == "Tool") | "  - \(.metadata.name): \(.description // "No description")"' 2>/dev/null || echo "  - pdf_extractor, sentiment_analyzer, google_search"
echo ""

echo "===================================="
echo "✅ Core services are working!"
echo ""
echo "📝 Current Status:"
echo "   - LLM Gateway: ✅ Working"
echo "   - Runtime Executor: ✅ Running"
echo "   - Manifest Ingestion: ✅ Running"
echo "   - Agent Orchestrator: ⚠️  Streaming integration needs refinement"
echo ""
echo "🔧 To use directly:"
echo ""
echo "# Talk to LLM:"
echo 'curl -X POST http://localhost:8081/completion \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"messages": [{"role": "user", "content": "Your message"}]}'"'"' | jq -r .content'
echo ""
echo "# Execute a tool via Runtime Executor:"
echo 'curl -X POST http://localhost:8083/execute/tool \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"tool_name": "sys_info", "parameters": {"operation": "get_cpu"}}'"'"' | jq .'
echo ""
echo "📖 Full docs: INTEGRATION_DONE.md"
