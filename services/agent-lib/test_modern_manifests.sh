#!/bin/bash
# Test script for modernized agent manifests

set -e

AGENT_LIB_DIR="/home/mlamkadm/repos/Cortex-Prime-MK1/services/agent-lib"
cd "$AGENT_LIB_DIR"

echo "=================================================="
echo "Testing Modern Agent Manifests with Streaming"
echo "=================================================="
echo ""

# Ensure agent-server is built
if [ ! -f "./agent-server" ]; then
    echo "❌ agent-server not found. Building..."
    make clean
    make -j4
    echo "✅ Build complete"
fi

echo ""
echo "Testing Manifest Loading..."
echo ""

# Test each agent manifest
test_agent() {
    local agent_name=$1
    local manifest_path=$2
    
    echo "-------------------------------------------"
    echo "Testing: $agent_name"
    echo "Manifest: $manifest_path"
    echo "-------------------------------------------"
    
    # Check if manifest exists
    if [ ! -f "$manifest_path" ]; then
        echo "❌ Manifest not found: $manifest_path"
        return 1
    fi
    
    echo "✅ Manifest file exists"
    
    # Validate YAML syntax
    if command -v yamllint &> /dev/null; then
        yamllint "$manifest_path" 2>&1 | head -5 || echo "⚠️  YAML validation warnings (non-fatal)"
    else
        echo "ℹ️  yamllint not available, skipping syntax check"
    fi
    
    # Check for required v1.0 fields
    echo ""
    echo "Checking v1.0 Sovereign Core Standard fields:"
    
    grep -q "^kind: Agent" "$manifest_path" && echo "  ✅ kind" || echo "  ❌ kind missing"
    grep -q "^version:" "$manifest_path" && echo "  ✅ version" || echo "  ❌ version missing"
    grep -q "^name:" "$manifest_path" && echo "  ✅ name" || echo "  ❌ name missing"
    grep -q "^summary:" "$manifest_path" && echo "  ✅ summary" || echo "  ❌ summary missing"
    grep -q "^streaming_protocol:" "$manifest_path" && echo "  ✅ streaming_protocol" || echo "  ⚠️  streaming_protocol not specified"
    grep -q "^context_feeds:" "$manifest_path" && echo "  ✅ context_feeds" || echo "  ℹ️  no context_feeds"
    grep -q "^tools:" "$manifest_path" && echo "  ✅ tools" || echo "  ℹ️  no tools"
    
    # Check for system prompt
    local prompt_file=$(grep "system_prompt:" "$manifest_path" | sed 's/.*: *"\(.*\)".*/\1/' | tr -d '"' | tr -d "'")
    if [ -n "$prompt_file" ]; then
        local prompt_path=$(dirname "$manifest_path")/"$prompt_file"
        if [ -f "$prompt_path" ]; then
            echo "  ✅ system_prompt file exists: $prompt_file"
        else
            echo "  ❌ system_prompt file not found: $prompt_path"
        fi
    fi
    
    echo ""
    echo "Streaming Protocol Features:"
    if grep -q "streaming_protocol: true" "$manifest_path"; then
        echo "  ✅ Streaming enabled"
        
        # Check if system prompt mentions streaming protocol
        if [ -n "$prompt_file" ] && [ -f "$prompt_path" ]; then
            if grep -q "<thought>" "$prompt_path" && grep -q "<action>" "$prompt_path" && grep -q "<response>" "$prompt_path"; then
                echo "  ✅ System prompt includes streaming protocol format"
            else
                echo "  ⚠️  System prompt may not include streaming protocol examples"
            fi
        fi
    else
        echo "  ℹ️  Streaming not enabled (legacy mode)"
    fi
    
    echo ""
}

# Test streaming example
test_agent "Streaming Example" "config/agents/streaming-example/agent.yml"

# Test Demurge
test_agent "Demurge (Creative Artificer)" "config/agents/demurge/agent.yml"

# Test Sage
test_agent "Sage (Wise Counsel)" "config/agents/sage/agent.yml"

echo ""
echo "=================================================="
echo "Summary"
echo "=================================================="
echo ""
echo "Modern manifests created:"
echo "  ✅ streaming-example - Basic streaming protocol demo"
echo "  ✅ demurge - Creative agent with streaming"
echo "  ✅ sage - Research agent with streaming"
echo ""
echo "Archived legacy manifests:"
echo "  📦 coder-agent-mk1"
echo "  📦 my_new_specialied_agent"
echo "  📦 standard-agent"
echo "  📦 standard-agent-MK1"
echo "  📦 standard-note-agent-MK1"
echo "  📦 tool-module-tester"
echo ""
echo "All in: config/agents/_archive/"
echo ""
echo "=================================================="
echo "Next Steps"
echo "=================================================="
echo ""
echo "To test an agent:"
echo "  export GEMINI_API_KEY='your-key'"
echo "  export AGENT_PROFILE_PATH='config/agents/demurge/agent.yml'"
echo "  ./agent-server"
echo ""
echo "Or use the agent programmatically in your C++ code."
echo ""
