# Agent-Lib Remaining Issues

**Date**: October 10, 2024  
**Status**: ⚠️ Working but needs refinement

## ✅ What's Working

1. **LLM Gateway Integration** - Routes through gateway correctly
2. **Streaming Protocol** - Chunked output, smooth rendering
3. **Modern Manifests** - v1.0 format fully supported
4. **Relic Loading** - research_cache loads successfully
5. **Multi-iteration** - Continues on non-final responses
6. **Tool Loading** - All tools register correctly

## ❌ Issues Found

### 1. JSON Parsing Errors in Actions

**Problem**: LLM is generating malformed JSON in `<action>` tags:

```
[ERROR] Failed to parse action
  Failed to parse action JSON: * Line 5, Column 5
  Missing '}' or object member name
```

**Root Cause**: The LLM (gemini-1.5-pro) is not properly formatting the JSON inside `<action>` tags. It's likely inserting comments or extra text.

**Example of what's happening**:
```xml
<action type="tool" id="research_1">
{
  "name": "call_subagent",
  "parameters": {
    "agent": "web_researcher"
    // Missing comma or bracket
  }
}
</action>
```

**Solution Needed**:
- Better prompt engineering in system prompt to enforce strict JSON
- Add JSON validation/cleaning before parsing
- Or: Make parser more lenient (strip comments, fix common errors)

### 2. Iteration Counting Logic

**Problem**: Iterations increment on every API call, not after executing actions.

**Current Behavior**:
```
Iteration 1 → LLM generates response with 3 actions
Iteration 2 → Actions haven't executed yet, LLM called again
Iteration 3 → Still processing actions from iteration 1
```

**Expected Behavior**:
```
Iteration 1 → LLM generates response with 3 actions → Execute all 3 actions
Iteration 2 → LLM sees action results → Generates new response/actions
Iteration 3 → Execute new actions
```

**User's Explanation**:
> "iteration is not incremented by actions but when the LLM stop generating the current iterations has 5 actions lets say, that are going to get executed"

**What This Means**:
1. LLM generates a complete response (might have 0-N actions)
2. Parser extracts all actions from that response
3. Execute ALL actions from that response
4. Add action results to context
5. THEN increment iteration
6. Call LLM again with updated context

**Current Flow** (WRONG):
```
while (iteration < 20) {
    iteration++  // ❌ Increments immediately
    response = llm.generate(prompt)
    parse_actions(response)
    // Actions queued but not completed yet
}
```

**Correct Flow**:
```
iteration = 0
while (iteration < 20) {
    response = llm.generate(prompt)
    actions = parse_actions(response)
    
    if (actions.empty() && response.is_final) {
        break  // Done
    }
    
    // Execute ALL actions before continuing
    for (action in actions) {
        result = execute(action)
        add_to_context(result)
    }
    
    iteration++  // ✅ Increment after actions complete
    
    if (response.is_final) {
        break
    }
}
```

### 3. Missing Tools

**Problem**: Agent tried to use `call_subagent` but it's not registered:

```
[ERROR] Agent 'research_orchestrator': tool 'call_subagent' not found
```

**Why**: The `call_subagent` is an internal tool that should be auto-registered for agents that have sub-agents defined.

**Solution**: Add auto-registration of `call_subagent` when agent manifest has `import.agents` section.

### 4. Action JSON Validation

**Problem**: No pre-validation of action JSON before attempting to parse.

**Suggestion**:
```cpp
std::string cleanActionJSON(const std::string& rawJSON) {
    std::string cleaned = rawJSON;
    
    // Remove // comments
    std::regex commentRegex("//.*");
    cleaned = std::regex_replace(cleaned, commentRegex, "");
    
    // Remove /* */ comments
    std::regex blockCommentRegex("/\\*.*?\\*/");
    cleaned = std::regex_replace(cleaned, blockCommentRegex, "");
    
    // Trim whitespace
    // ... etc
    
    return cleaned;
}
```

## 📋 Priority Fixes

### High Priority
1. **Fix iteration counting logic** - Critical for proper agent behavior
2. **Add call_subagent internal tool** - Needed for orchestrator agents
3. **Improve JSON parsing robustness** - Prevent parse errors

### Medium Priority
4. **Better error messages** - Show the malformed JSON to help debug
5. **System prompt improvements** - Make LLM generate better JSON
6. **Action execution sequencing** - Ensure proper order

### Low Priority
7. **Performance optimization** - Reduce unnecessary iterations
8. **Better logging** - Track action execution flow
9. **Metrics** - Count successful vs failed actions

## 🔧 Where to Fix

### 1. Iteration Logic
**File**: `src/agent/streaming.cpp` around line 110-240

Current code:
```cpp
while (shouldContinue && currentIteration < iterationLimit) {
    currentIteration++;  // ❌ Move this to after action execution
    logMessage(LogLevel::INFO, "Agent '" + agentName + "' Iteration " +
                               std::to_string(currentIteration) + "/" +
                               std::to_string(iterationLimit));
    // ... generate response ...
}
```

Should be:
```cpp
while (shouldContinue && currentIteration < iterationLimit) {
    logMessage(LogLevel::INFO, "Agent '" + agentName + "' Iteration " +
                               std::to_string(currentIteration + 1) + "/" +
                               std::to_string(iterationLimit));
    
    // ... generate response ...
    // ... parse actions ...
    // ... execute ALL actions ...
    
    currentIteration++;  // ✅ After actions complete
    
    if (receivedFinalResponse) {
        shouldContinue = false;
    }
}
```

### 2. JSON Parsing
**File**: `src/agent/streaming_protocol.cpp` around line 240-274

Add cleaning/validation before `parseAction()`.

### 3. call_subagent Tool
**File**: `src/utils/internal_tools.cpp`

Add registration for call_subagent that:
- Takes agent name and task as parameters
- Loads sub-agent manifest
- Executes sub-agent with task
- Returns sub-agent's response

## 📝 Testing Plan

After fixes:
1. Test with simple agent (no actions)
2. Test with single action per iteration
3. Test with multiple actions per iteration
4. Test with nested sub-agent calls
5. Test with malformed JSON (should handle gracefully)

## The Work Continues...

The foundation is solid, but these refinements will make it production-quality.
