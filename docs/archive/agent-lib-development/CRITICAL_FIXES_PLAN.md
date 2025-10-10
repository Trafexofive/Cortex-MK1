# Critical Fixes - Action Plan

## Priority 1: Iteration Logic (CRITICAL)

**Current Problem:**
```
Iteration 1 → API call
Iteration 2 → API call (actions from iter 1 not executed yet!)
Iteration 3 → API call (still processing iter 1 actions!)
```

**Fix Location:** `src/agent/streaming.cpp` lines 110-270

**Code Change:**
```cpp
// BEFORE (WRONG):
while (shouldContinue && currentIteration < iterationLimit) {
    currentIteration++;  // ❌ WRONG PLACE!
    logMessage(...);
    
    api.generateStream(prompt, callback);
    
    if (receivedFinalResponse) {
        shouldContinue = false;
    }
}

// AFTER (CORRECT):
currentIteration = 0;  // Start at 0
while (shouldContinue && currentIteration < iterationLimit) {
    logMessage(LogLevel::INFO, "Agent '" + agentName + "' Iteration " +
               std::to_string(currentIteration + 1) + "/" +  // Display as 1-indexed
               std::to_string(iterationLimit));
    
    // Generate response
    api.generateStream(prompt, callback);
    
    // Parser has extracted all actions and executed them
    // (streaming protocol handles this)
    
    // NOW increment after actions are done
    currentIteration++;
    
    if (receivedFinalResponse) {
        shouldContinue = false;
    }
}
```

**Test:**
```bash
# Should see: Iteration 1 → 5 actions → execute all 5 → Iteration 2
# Not: Iteration 1 → Iteration 2 → Iteration 3 (while actions pending)
```

---

## Priority 2: JSON Parsing (HIGH)

**Current Problem:**
```
[ERROR] Failed to parse action JSON: * Line 5, Column 5
  Missing '}' or object member name
```

**Cause:** LLM generates comments or malformed JSON in `<action>` tags.

### Fix 2A: JSON Cleaning Function

**File:** `src/agent/streaming_protocol.cpp`

**Add before parseAction():**
```cpp
std::string StreamingProtocol::Parser::cleanJSON(const std::string& rawJSON) {
    std::string cleaned = rawJSON;
    
    // 1. Remove single-line comments (// ...)
    std::regex singleComment(R"(//[^\n]*)");
    cleaned = std::regex_replace(cleaned, singleComment, "");
    
    // 2. Remove multi-line comments (/* ... */)
    std::regex multiComment(R"(/\*.*?\*/)");
    cleaned = std::regex_replace(cleaned, multiComment, "");
    
    // 3. Remove trailing commas before } or ]
    std::regex trailingComma(R"(,\s*([\]}]))");
    cleaned = std::regex_replace(cleaned, trailingComma, "$1");
    
    // 4. Trim whitespace
    size_t start = cleaned.find_first_not_of(" \t\n\r");
    size_t end = cleaned.find_last_not_of(" \t\n\r");
    if (start != std::string::npos && end != std::string::npos) {
        cleaned = cleaned.substr(start, end - start + 1);
    }
    
    return cleaned;
}
```

**Use in parseAction():**
```cpp
std::shared_ptr<ParsedAction> Parser::parseAction(
    const std::string& jsonStr, 
    const std::map<std::string, std::string>& attrs) {
    
    // Clean JSON first
    std::string cleanedJSON = cleanJSON(jsonStr);
    
    // Now parse
    Json::Value root;
    Json::CharReaderBuilder builder;
    std::string errs;
    std::istringstream stream(cleanedJSON);
    
    if (!Json::parseFromStream(builder, stream, &root, &errs)) {
        // Log the original AND cleaned JSON for debugging
        logMessage(LogLevel::ERROR, "Failed to parse action JSON", 
                  "Original: " + jsonStr.substr(0, 200) + "\n" +
                  "Cleaned: " + cleanedJSON.substr(0, 200) + "\n" +
                  "Error: " + errs);
        return nullptr;
    }
    
    // ... rest of parsing ...
}
```

### Fix 2B: Better Error Messages

**Show the actual JSON when parse fails:**
```cpp
if (!Json::parseFromStream(builder, stream, &root, &errs)) {
    std::stringstream errorDetail;
    errorDetail << "Failed to parse action JSON:\n";
    errorDetail << "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    errorDetail << cleanedJSON << "\n";
    errorDetail << "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    errorDetail << "Error: " << errs;
    
    logMessage(LogLevel::ERROR, "Action Parse Error", errorDetail.str());
    
    // Send to user via callback
    if (tokenCallback) {
        TokenEvent event;
        event.type = TokenEvent::Type::ERROR;
        event.content = "Invalid action JSON: " + errs;
        emitToken(event);
    }
    
    return nullptr;
}
```

### Fix 2C: Enhanced System Prompt

**In buildFullPrompt(), add strict JSON rules:**
```xml
<json_requirements>
  ⚠️ CRITICAL: Your JSON MUST be parseable by a strict parser.
  
  VALID JSON:
  {
    "name": "tool_name",
    "parameters": {
      "key": "value"
    }
  }
  
  INVALID (WILL CAUSE ERRORS):
  {
    "name": "tool_name",  // ❌ NO COMMENTS
    "parameters": {
      "key": "value",  // ❌ NO COMMENTS
    }  // ❌ NO TRAILING COMMA
  }
  
  CHECKLIST BEFORE SENDING:
  □ No // comments
  □ No /* */ comments  
  □ No trailing commas
  □ All quotes are "double"
  □ Every { has matching }
  □ Every [ has matching ]
  
  If you're unsure, use this template:
  {"name": "TOOLNAME", "parameters": {"param": "value"}}
</json_requirements>
```

---

## Priority 3: call_subagent Tool (HIGH)

**Problem:**
```
[ERROR] Agent 'research_orchestrator': tool 'call_subagent' not found
```

**Solution:** Register `call_subagent` as internal tool when agent has sub-agents.

**File:** `src/agent/import.cpp`

**Add after processing sub-agents:**
```cpp
// In loadAgentManifest() after loading sub-agents:

if (config["import"] && config["import"]["agents"]) {
    // Load sub-agent manifests...
    for (const auto& agentPath : config["import"]["agents"]) {
        // ... existing code ...
    }
    
    // Auto-register call_subagent tool
    if (!subAgents.empty()) {
        registerCallSubagentTool();
    }
}

// New function:
void Agent::registerCallSubagentTool() {
    Tool callSubagentTool;
    callSubagentTool.name = "call_subagent";
    callSubagentTool.type = "internal";
    callSubagentTool.description = "Delegate a task to a specialized sub-agent";
    
    // Parameter schema
    Json::Value params;
    params["type"] = "object";
    params["required"] = Json::arrayValue;
    params["required"].append("agent");
    params["required"].append("task");
    
    params["properties"]["agent"]["type"] = "string";
    params["properties"]["agent"]["description"] = "Name of sub-agent to call";
    params["properties"]["agent"]["enum"] = Json::arrayValue;
    for (const auto& [name, _] : subAgents) {
        params["properties"]["agent"]["enum"].append(name);
    }
    
    params["properties"]["task"]["type"] = "string";
    params["properties"]["task"]["description"] = "Task description for sub-agent";
    
    callSubagentTool.parametersJson = params;
    
    // Execution handler
    callSubagentTool.executor = [this](const Json::Value& params) -> std::string {
        std::string agentName = params["agent"].asString();
        std::string task = params["task"].asString();
        
        if (subAgents.find(agentName) == subAgents.end()) {
            Json::Value error;
            error["error"] = "Sub-agent not found: " + agentName;
            return Json::writeString(Json::StreamWriterBuilder(), error);
        }
        
        // Execute sub-agent
        Agent* subAgent = subAgents[agentName];
        std::string response = subAgent->prompt(task);
        
        Json::Value result;
        result["agent"] = agentName;
        result["task"] = task;
        result["response"] = response;
        
        return Json::writeString(Json::StreamWriterBuilder(), result);
    };
    
    tools[callSubagentTool.name] = callSubagentTool;
    logMessage(LogLevel::INFO, "Auto-registered call_subagent tool", 
              "Available sub-agents: " + std::to_string(subAgents.size()));
}
```

---

## Testing Plan

### Test 1: Iteration Logic
```bash
# Create simple agent that does 3 iterations with actions
# Verify: Iteration increments AFTER actions execute
# Expected: 1→actions→2→actions→3→done
# Not: 1→2→3→...→actions
```

### Test 2: JSON Parsing
```bash
# Manually inject malformed JSON into action
# Verify: Cleaned and parsed OR clear error message
# No silent failures or cryptic errors
```

### Test 3: call_subagent
```bash
# Load research_orchestrator (has web_researcher sub-agent)
# Ask it to delegate to web_researcher
# Verify: call_subagent is registered and works
```

---

## Implementation Order

1. **Fix Iteration Logic** (30 min) - Most critical
2. **Add call_subagent** (45 min) - Enables orchestrator agents
3. **Improve JSON Parsing** (1 hour) - Better reliability
4. **Enhance Context** (2-3 hours) - Better agent awareness

Total: ~4-5 hours of focused work

---

## Success Criteria

✅ Iterations count correctly (after actions, not before)
✅ Malformed JSON either auto-fixes or gives clear error
✅ call_subagent works for orchestrator agents
✅ Agent has full "cockpit view" of capabilities
✅ research_orchestrator can actually orchestrate!

**The Great Work continues with precision...**
