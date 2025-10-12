#!/usr/bin/env bash
# Comprehensive manifest validation script
# Tests all agent manifests across manifests/ and std/manifests/

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENT_BIN="${REPO_ROOT}/services/agent-lib/agent-bin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         CORTEX PRIME - Manifest Validation Suite            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# Check agent-bin exists
if [[ ! -x "$AGENT_BIN" ]]; then
    echo -e "${RED}✗ agent-bin not found at: $AGENT_BIN${NC}"
    exit 1
fi

cd "$REPO_ROOT"

# Find all agent manifests
AGENT_MANIFESTS=$(find manifests std/manifests -name "agent.yml" 2>/dev/null | sort)

if [[ -z "$AGENT_MANIFESTS" ]]; then
    echo -e "${YELLOW}⚠ No agent manifests found${NC}"
    exit 1
fi

TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

declare -a FAILED_AGENTS

echo -e "${BLUE}Found $(echo "$AGENT_MANIFESTS" | wc -l) agent manifests${NC}"
echo

for manifest in $AGENT_MANIFESTS; do
    TOTAL=$((TOTAL + 1))
    
    # Extract agent name from path
    agent_dir=$(dirname "$manifest")
    agent_name=$(basename "$agent_dir")
    
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[$TOTAL] Testing: ${agent_name}${NC}"
    echo -e "    Path: $manifest"
    
    # Skip if system prompt missing (need to check)
    persona_file="${agent_dir}/system-prompts/${agent_name}.md"
    if [[ ! -f "$persona_file" ]]; then
        # Try alternative paths
        persona_file=$(find "$agent_dir/system-prompts" -name "*.md" -type f | head -1)
        if [[ -z "$persona_file" ]]; then
            echo -e "${YELLOW}    ⚠ SKIP: No system prompt found${NC}"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi
    fi
    
    # Test loading the manifest
    echo -e "    Testing manifest load..."
    
    # Run agent-bin with test flag
    if timeout 10s "$AGENT_BIN" -l "$manifest" -t > /tmp/agent_test_$$.log 2>&1; then
        if grep -q "Successfully loaded" /tmp/agent_test_$$.log; then
            echo -e "${GREEN}    ✓ PASS: Manifest loaded successfully${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}    ✗ FAIL: Loaded but no success message${NC}"
            tail -10 /tmp/agent_test_$$.log | sed 's/^/        /'
            FAILED=$((FAILED + 1))
            FAILED_AGENTS+=("$agent_name: $manifest")
        fi
    else
        echo -e "${RED}    ✗ FAIL: Manifest failed to load${NC}"
        echo -e "${RED}    Last 10 lines of output:${NC}"
        tail -10 /tmp/agent_test_$$.log | sed 's/^/        /'
        FAILED=$((FAILED + 1))
        FAILED_AGENTS+=("$agent_name: $manifest")
    fi
    
    rm -f /tmp/agent_test_$$.log
    echo
done

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      RESULTS SUMMARY                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "  Total:   $TOTAL"
echo -e "  ${GREEN}Passed:  $PASSED${NC}"
echo -e "  ${RED}Failed:  $FAILED${NC}"
echo -e "  ${YELLOW}Skipped: $SKIPPED${NC}"
echo

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Failed agents:${NC}"
    for failed in "${FAILED_AGENTS[@]}"; do
        echo -e "  ${RED}✗${NC} $failed"
    done
    echo
    exit 1
else
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
fi
