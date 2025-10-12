#!/bin/bash
# ==============================================================================
# AGENT-LIB COMPREHENSIVE TEST SUITE
# ==============================================================================
# Tests modern manifest loading, tool execution, and agent functionality
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

log_section() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ==============================================================================
# Test 1: Build System
# ==============================================================================
test_build() {
    log_section "TEST 1: Build System"
    
    log_info "Cleaning build artifacts..."
    make clean > /dev/null 2>&1
    
    log_info "Building agent-bin..."
    if make bin 2>&1 | grep -q "built successfully"; then
        log_success "agent-bin built successfully"
    else
        log_error "agent-bin build failed"
    fi
    
    if [ -x "./agent-bin" ]; then
        log_success "agent-bin executable exists and is executable"
    else
        log_error "agent-bin not executable"
    fi
    
    SIZE=$(stat -f%z "./agent-bin" 2>/dev/null || stat -c%s "./agent-bin" 2>/dev/null || echo "0")
    if [ "$SIZE" -gt 1000000 ]; then
        log_success "agent-bin size is reasonable ($SIZE bytes)"
    else
        log_error "agent-bin size seems too small ($SIZE bytes)"
    fi
}

# ==============================================================================
# Test 2: Manifest Validation
# ==============================================================================
test_manifests() {
    log_section "TEST 2: Manifest Validation"
    
    # Test Sage manifest
    log_info "Validating Sage agent manifest..."
    if [ -f "config/agents/sage/agent.yml" ]; then
        log_success "Sage manifest exists"
        
        # Check required v1.0 fields
        if grep -q "kind: Agent" config/agents/sage/agent.yml; then
            log_success "Sage manifest has 'kind: Agent'"
        else
            log_error "Sage manifest missing 'kind: Agent'"
        fi
        
        if grep -q "cognitive_engine:" config/agents/sage/agent.yml; then
            log_success "Sage manifest has cognitive_engine section"
        else
            log_error "Sage manifest missing cognitive_engine section"
        fi
    else
        log_error "Sage manifest not found"
    fi
    
    # Test Demurge manifest
    log_info "Validating Demurge agent manifest..."
    if [ -f "config/agents/demurge/agent.yml" ]; then
        log_success "Demurge manifest exists"
        
        if grep -q "kind: Agent" config/agents/demurge/agent.yml; then
            log_success "Demurge manifest has 'kind: Agent'"
        else
            log_error "Demurge manifest missing 'kind: Agent'"
        fi
    else
        log_error "Demurge manifest not found"
    fi
    
    # Test tool manifests
    log_info "Validating tool manifests..."
    local tool_count=0
    for tool in config/agents/*/tools/*/tool.yml; do
        if [ -f "$tool" ]; then
            ((tool_count++))
            if grep -q "kind: Tool" "$tool"; then
                log_success "Tool manifest valid: $(basename $(dirname $tool))"
            else
                log_error "Tool manifest invalid: $(basename $(dirname $tool))"
            fi
        fi
    done
    
    if [ $tool_count -gt 0 ]; then
        log_success "Found $tool_count tool manifests"
    else
        log_error "No tool manifests found"
    fi
}

# ==============================================================================
# Test 3: Tool Scripts
# ==============================================================================
test_tool_scripts() {
    log_section "TEST 3: Tool Scripts"
    
    # Test knowledge_retriever
    log_info "Testing knowledge_retriever tool..."
    local script="config/agents/sage/tools/knowledge_retriever/scripts/knowledge_retriever.py"
    if [ -x "$script" ]; then
        log_success "knowledge_retriever script is executable"
        
        # Test execution with sample input (as command-line argument)
        local result=$(python3 "$script" '{"query": "recursion", "depth": "quick"}' 2>&1)
        if echo "$result" | grep -q "success.*true\|definition\|results"; then
            log_success "knowledge_retriever produces valid output"
        else
            log_error "knowledge_retriever output invalid: $result"
        fi
    else
        log_error "knowledge_retriever script not executable"
    fi
    
    # Test fact_checker
    log_info "Testing fact_checker tool..."
    local script="config/agents/sage/tools/fact_checker/scripts/fact_checker.py"
    if [ -x "$script" ]; then
        log_success "fact_checker script is executable"
        
        local result=$(python3 "$script" '{"claim": "The sky is blue", "context": "general knowledge"}' 2>&1)
        if echo "$result" | grep -q "success.*true\|plausible\|verdict"; then
            log_success "fact_checker produces valid output"
        else
            log_error "fact_checker output invalid: $result"
        fi
    else
        log_error "fact_checker script not executable"
    fi
    
    # Test code_generator
    log_info "Testing code_generator tool..."
    local script="config/agents/demurge/tools/code_generator/scripts/code_generator.py"
    if [ -x "$script" ]; then
        log_success "code_generator script is executable"
        
        local result=$(python3 "$script" '{"language": "python", "task": "hello world"}' 2>&1)
        if echo "$result" | grep -q "success.*true\|code\|generated"; then
            log_success "code_generator produces valid output"
        else
            log_error "code_generator output invalid: $result"
        fi
    else
        log_error "code_generator script not executable"
    fi
}

# ==============================================================================
# Test 4: Agent Loading
# ==============================================================================
test_agent_loading() {
    log_section "TEST 4: Agent Loading (CLI Test)"
    
    log_info "Testing Sage agent loading..."
    
    # Create test input file
    cat > /tmp/agent-test-input.txt <<EOF
/load config/agents/sage/agent.yml
/info
/tools
/quit
EOF
    
    # Run agent-bin with test input
    local output=$(./agent-bin < /tmp/agent-test-input.txt 2>&1)
    
    if echo "$output" | grep -q "Successfully loaded agent profile: sage"; then
        log_success "Sage agent loaded successfully"
    else
        log_error "Sage agent failed to load"
    fi
    
    if echo "$output" | grep -q "knowledge_retriever"; then
        log_success "Sage tools loaded (knowledge_retriever found)"
    else
        log_error "Sage tools not loaded properly"
    fi
    
    if echo "$output" | grep -q "fact_checker"; then
        log_success "Sage tools loaded (fact_checker found)"
    else
        log_error "Sage tools not loaded properly"
    fi
    
    # Test Demurge
    log_info "Testing Demurge agent loading..."
    
    cat > /tmp/agent-test-input.txt <<EOF
/load config/agents/demurge/agent.yml
/info
/tools
/quit
EOF
    
    output=$(./agent-bin < /tmp/agent-test-input.txt 2>&1)
    
    if echo "$output" | grep -q "Successfully loaded agent profile: demurge"; then
        log_success "Demurge agent loaded successfully"
    else
        log_error "Demurge agent failed to load"
    fi
    
    if echo "$output" | grep -q "code_generator"; then
        log_success "Demurge tools loaded (code_generator found)"
    else
        log_error "Demurge tools not loaded properly"
    fi
    
    # Cleanup
    rm -f /tmp/agent-test-input.txt
}

# ==============================================================================
# Test 5: Cognitive Engine Configuration
# ==============================================================================
test_cognitive_engine() {
    log_section "TEST 5: Cognitive Engine Configuration"
    
    log_info "Testing cognitive_engine parsing..."
    
    cat > /tmp/agent-test-input.txt <<EOF
/load config/agents/sage/agent.yml
/quit
EOF
    
    local output=$(./agent-bin < /tmp/agent-test-input.txt 2>&1)
    
    if echo "$output" | grep -q "Model 'gemini-2.0-flash'"; then
        log_success "Cognitive engine model parsed correctly"
    else
        log_error "Cognitive engine model not parsed"
    fi
    
    if echo "$output" | grep -q "Temperature 0.3"; then
        log_success "Cognitive engine temperature parsed correctly"
    else
        log_error "Cognitive engine temperature not parsed"
    fi
    
    if echo "$output" | grep -q "Token limit 8192"; then
        log_success "Cognitive engine token limit parsed correctly"
    else
        log_error "Cognitive engine token limit not parsed"
    fi
    
    rm -f /tmp/agent-test-input.txt
}

# ==============================================================================
# Test 6: Context Feeds
# ==============================================================================
test_context_feeds() {
    log_section "TEST 6: Context Feeds"
    
    log_info "Testing context feed loading..."
    
    cat > /tmp/agent-test-input.txt <<EOF
/load config/agents/sage/agent.yml
/quit
EOF
    
    local output=$(./agent-bin < /tmp/agent-test-input.txt 2>&1)
    
    if echo "$output" | grep -q "Loaded context feed 'current_datetime'"; then
        log_success "Context feed 'current_datetime' loaded"
    else
        log_error "Context feed 'current_datetime' not loaded"
    fi
    
    if echo "$output" | grep -q "Loaded context feed 'research_session'"; then
        log_success "Context feed 'research_session' loaded"
    else
        log_error "Context feed 'research_session' not loaded"
    fi
    
    rm -f /tmp/agent-test-input.txt
}

# ==============================================================================
# Test 7: Environment Variables
# ==============================================================================
test_environment() {
    log_section "TEST 7: Environment Variables"
    
    log_info "Testing environment variable loading..."
    
    cat > /tmp/agent-test-input.txt <<EOF
/load config/agents/sage/agent.yml
/quit
EOF
    
    local output=$(./agent-bin < /tmp/agent-test-input.txt 2>&1)
    
    if echo "$output" | grep -q "RESEARCH_DIR"; then
        log_success "Environment variable RESEARCH_DIR loaded"
    else
        log_error "Environment variable RESEARCH_DIR not loaded"
    fi
    
    if echo "$output" | grep -q "KNOWLEDGE_BASE"; then
        log_success "Environment variable KNOWLEDGE_BASE loaded"
    else
        log_error "Environment variable KNOWLEDGE_BASE not loaded"
    fi
    
    if echo "$output" | grep -q "VERIFY_SOURCES"; then
        log_success "Environment variable VERIFY_SOURCES loaded"
    else
        log_error "Environment variable VERIFY_SOURCES not loaded"
    fi
    
    rm -f /tmp/agent-test-input.txt
}

# ==============================================================================
# Test 8: System Prompts
# ==============================================================================
test_system_prompts() {
    log_section "TEST 8: System Prompts"
    
    log_info "Checking system prompt files..."
    
    if [ -f "config/agents/sage/system-prompts/sage.md" ]; then
        log_success "Sage system prompt exists"
        
        if grep -q "streaming" config/agents/sage/system-prompts/sage.md 2>/dev/null || \
           grep -q "Sage" config/agents/sage/system-prompts/sage.md 2>/dev/null; then
            log_success "Sage system prompt has content"
        else
            log_error "Sage system prompt is empty or invalid"
        fi
    else
        log_error "Sage system prompt not found"
    fi
    
    if [ -f "config/agents/demurge/system-prompts/demurge.md" ]; then
        log_success "Demurge system prompt exists"
        
        if grep -q "streaming" config/agents/demurge/system-prompts/demurge.md 2>/dev/null || \
           grep -q "Demurge" config/agents/demurge/system-prompts/demurge.md 2>/dev/null; then
            log_success "Demurge system prompt has content"
        else
            log_error "Demurge system prompt is empty or invalid"
        fi
    else
        log_error "Demurge system prompt not found"
    fi
}

# ==============================================================================
# Main Test Execution
# ==============================================================================
main() {
    log_section "AGENT-LIB TEST SUITE v1.0"
    log_info "Starting comprehensive tests..."
    echo ""
    
    # Run all tests
    test_build
    test_manifests
    test_tool_scripts
    test_agent_loading
    test_cognitive_engine
    test_context_feeds
    test_environment
    test_system_prompts
    
    # Print summary
    log_section "TEST SUMMARY"
    echo ""
    echo -e "Total Tests:  ${BLUE}$TESTS_TOTAL${NC}"
    echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║     ALL TESTS PASSED! ✓                ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        return 0
    else
        echo -e "${RED}╔════════════════════════════════════════╗${NC}"
        echo -e "${RED}║     SOME TESTS FAILED ✗                ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════╝${NC}"
        return 1
    fi
}

# Run main function
main
exit $?
