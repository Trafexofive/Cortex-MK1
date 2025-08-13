#!/bin/bash
# execute_bash.sh - Agent bash command executor with rich context
set -euo pipefail

PARAMS_JSON="$1"
[ -z "$PARAMS_JSON" ] && { echo "BASH_TOOL_ERROR: No JSON parameters provided" >&2; exit 1; }

# Extract command with error context
COMMAND=$(jq -er .command <<< "$PARAMS_JSON" 2>/dev/null) || {
    echo "BASH_TOOL_ERROR: Failed to parse JSON or extract 'command' field" >&2
    echo "BASH_TOOL_INPUT: $PARAMS_JSON" >&2
    exit 1
}

# Rich execution context for agent parsing
echo "BASH_TOOL_START: $(date '+%Y-%m-%d %H:%M:%S')" >&2
echo "BASH_TOOL_COMMAND: $COMMAND" >&2
echo "BASH_TOOL_PWD: $(pwd)" >&2
echo "BASH_TOOL_USER: $(whoami)" >&2
echo "BASH_TOOL_OUTPUT_BEGIN" >&2

# Execute with timing and exit status capture
START_TIME=$(date +%s.%N)
bash -c "$COMMAND"
EXIT_STATUS=$?
END_TIME=$(date +%s.%N)

# Post-execution context
DURATION=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "unknown")
echo "BASH_TOOL_OUTPUT_END" >&2
echo "BASH_TOOL_EXIT_STATUS: $EXIT_STATUS" >&2
echo "BASH_TOOL_DURATION: ${DURATION}s" >&2
echo "BASH_TOOL_FINISH: $(date '+%Y-%m-%d %H:%M:%S')" >&2

exit $EXIT_STATUS
