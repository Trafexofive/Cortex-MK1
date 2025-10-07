#!/bin/bash
# ==============================================================================
# PROJECT: CORTEX-PRIME - Universal Test Client v1.0
#
# A fully featured client for testing the API gateway and other services.
# ==============================================================================

set -euo pipefail

# --- Configuration ---
GATEWAY_HOST=${GATEWAY_HOST:-localhost}
GATEWAY_PORT=${GATEWAY_PORT:-8001}
BASE_URL="http://${GATEWAY_HOST}:${GATEWAY_PORT}"

# --- Helper Functions ---
function print_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  health          Check the health of the API gateway."
    echo "  capabilities    Get the capabilities of the API gateway."
    echo "  chat <prompt>   Send a text prompt to the agent."
    echo "  text <prompt>   Alias for chat."
    echo "  voice           Interact with the voice stream endpoint."
    echo ""
}

function health_check() {
    echo "Pinging API gateway at ${BASE_URL}/health..."
    curl -s -X GET "${BASE_URL}/health" | jq .
}

function get_capabilities() {
    echo "Getting system capabilities from ${BASE_URL}/system/capabilities..."
    curl -s -X GET "${BASE_URL}/system/capabilities" | jq .
}

function send_chat() {
    local prompt="$@"

    if [[ -z "$prompt" ]]; then
        echo "Usage: $0 chat <prompt>" >&2
        echo "Error: Prompt cannot be empty." >&2
        return 1
    fi

    local payload
    payload=$(jq -n --arg prompt "$prompt" '{prompt: $prompt, agent_name: "journaler"}')

    curl -s -X POST "${BASE_URL}/api/v1/agent/prompt" \
        -H "Content-Type: application/json" \
        -d "$payload"
}


function voice_stream() {
    echo "Connecting to voice stream at ${BASE_URL/http/ws}/v1/inference/stream..."
    echo "This requires websocat (wscat) to be installed."
    
    if ! command -v wscat &> /dev/null; then
        echo "wscat could not be found. Please install it to use the voice stream." >&2
        return 1
    fi

    # This is a placeholder for a more complex interaction
    # A real implementation would need to handle audio streaming
    wscat -c "${BASE_URL/http/ws}/v1/inference/stream"
}


# --- Main Dispatcher ---
COMMAND=$1
shift || true

case "$COMMAND" in
    health)
        health_check
        ;;
    capabilities)
        get_capabilities
        ;;
    chat|text)
        send_chat $@
        ;;
    voice)
        voice_stream
        ;;
    *)
        print_usage
        exit 1
        ;;
esac