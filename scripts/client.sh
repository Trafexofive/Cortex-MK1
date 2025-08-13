#!/bin/bash
# ==============================================================================
# PROJECT: CORTEX-PRIME - Universal Test Client v1.0
#
# A fully featured client for testing the API gateway and other services.
# ==============================================================================

set -euo pipefail

# --- Configuration ---
GATEWAY_HOST=${GATEWAY_HOST:-localhost}
GATEWAY_PORT=${GATEWAY_PORT:-8080}
BASE_URL="http://${GATEWAY_HOST}:${GATEWAY_PORT}"

# --- Helper Functions ---
function print_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  health          Check the health of the API gateway."
    echo "  capabilities    Get the capabilities of the API gateway."
    echo "  chat            Send a chat completion request."
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
    local provider=$1
    local model=$2
    local prompt=$3

    if [[ -z "$provider" || -z "$model" || -z "$prompt" ]]; then
        echo "Usage: $0 chat <provider> <model> <prompt>" >&2
        return 1
    fi

    local request_body
    request_body=$(jq -n --arg provider "$provider" --arg model "$model" --arg content "$prompt" \
        '{
            "provider": $provider,
            "model": $model,
            "input": {
                "messages": [
                    {"role": "user", "content": $content}
                ]
            }
        }')

    echo "Sending chat request to ${BASE_URL}/v1/inference..."
    curl -s -X POST "${BASE_URL}/v1/inference" \
        -H "Content-Type: application/json" \
        -d "$request_body" | jq .
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
    chat)
        send_chat "$@"
        ;;
    voice)
        voice_stream
        ;;
    *)
        print_usage
        exit 1
        ;;
esac