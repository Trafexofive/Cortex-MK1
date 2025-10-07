#!/bin/bash
# ==============================================================================
# Chimera Core - Integration Test Script
# ==============================================================================

set -e

CORE_URL="http://localhost:8001"

# Helper function to check for endpoint availability
wait_for_service() {
    echo -n "Waiting for $1 to be available..."
    until curl -s -f "$2" > /dev/null; do
        echo -n "."
        sleep 2
    done
    echo " [OK]"
}

# Helper function for running a test
run_test() {
    local test_name=$1
    local command=$2
    echo -n "- Running test: '$test_name'... "
    if eval "$command"; then
        echo -e "\033[0;32m[PASSED]\033[0m"
    else
        echo -e "\033[0;31m[FAILED]\033[0m"
        exit 1
    fi
}

# --- Main Test Execution ---

# 1. Wait for Chimera Core to be healthy
wait_for_service "Chimera Core" "${CORE_URL}/health"

# 2. Test Agent Registry
run_test "Agent Registry contains 'journaler'" \
    "curl -s -f '${CORE_URL}/system/registries/agents' | jq -e '.journaler' > /dev/null"

# 3. Test Tool Registry
run_test "Tool Registry contains 'sys_info'" \
    "curl -s -f '${CORE_URL}/system/registries/tools' | jq -e '.sys_info' > /dev/null"

run_test "Tool Registry contains local 'calendar' tool" \
    "curl -s -f '${CORE_URL}/system/registries/tools' | jq -e '.calendar' > /dev/null"

# 4. Test Relic Registry
run_test "Relic Registry contains 'kv_store'" \
    "curl -s -f '${CORE_URL}/system/registries/relics' | jq -e '.kv_store' > /dev/null"

# 5. Verify path resolution for a tool
run_test "Tool 'sys_info' has resolved absolute script path" \
    "curl -s -f '${CORE_URL}/system/registries/tools' | jq -e '.sys_info.path | test(\"/app/tools/sys_info/scripts/sys_info.py$\")' > /dev/null"


echo -e "\n\033[0;32mAll Chimera Core integration tests passed successfully!\033[0m"
