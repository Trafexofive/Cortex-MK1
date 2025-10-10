# Agent Context Enhancement Plan

## The "Cockpit" Problem

**Issue**: Agents don't have enough context about their environment, capabilities, and current state.

**User's Insight**: 
> "The agent doesn't have enough context (be it static or dynamic) in order to feel comfy in its suite/cockpit"

## What Agents Currently Know

Minimal context:
- Their name
- System prompt
- User's message
- Tool definitions (basic)

## What Agents SHOULD Know

### Static Context (One-time, at startup)
1. **Identity & Capabilities**
   - Full agent manifest (name, description, purpose)
   - Complete tool list with detailed descriptions
   - Available relics and their endpoints
   - Sub-agents available for delegation
   - Environment variables and workspace paths

2. **Operational Guidelines**
   - Iteration limit (current/max)
   - Resource constraints
   - Allowed actions
   - Protocol requirements (streaming format)

3. **Tool Documentation**
   - Each tool's full parameter schema
   - Example usage for each tool
   - Success/error patterns
   - When to use which tool

### Dynamic Context (Updated each iteration)
1. **State Information**
   - Current iteration number
   - Actions executed so far
   - Action results from previous iterations
   - Context feed values (refreshed)
   - Timestamp/datetime

2. **Progress Tracking**
   - What tasks have been completed
   - What's pending
   - Error history
   - Success rate

3. **Resource Status**
   - Relic health status
   - Available tokens remaining
   - Time elapsed
   - Cache hit/miss ratios

## Implementation: Enhanced Context Injection

### 1. Add Static Context Section

**In buildFullPrompt()**, add after system prompt:

```xml
<agent_cockpit>
  <identity>
    <name>research_orchestrator</name>
    <role>Master research coordinator</role>
    <iteration_limit>20</iteration_limit>
    <current_iteration>3</current_iteration>
    <workspace>/home/mlamkadm/research/</workspace>
  </identity>

  <capabilities>
    <tools>
      <tool name="pdf_extractor">
        <description>Extracts text and metadata from PDF files</description>
        <when_to_use>When user provides PDF or asks about document content</when_to_use>
        <parameters>
          <param name="file_path" type="string" required="true">Path to PDF</param>
          <param name="extract_images" type="boolean" default="false">Include images</param>
        </parameters>
        <example>
          {"name": "pdf_extractor", "parameters": {"file_path": "/path/to/doc.pdf"}}
        </example>
      </tool>
      <!-- More tools... -->
    </tools>

    <relics>
      <relic name="research_cache" status="healthy">
        <type>vector_database</type>
        <endpoints>
          <endpoint name="store" method="POST" path="/store"/>
          <endpoint name="search" method="POST" path="/search"/>
        </endpoints>
        <when_to_use>Store/retrieve research findings for reuse</when_to_use>
      </relic>
    </relics>

    <sub_agents>
      <agent name="web_researcher">
        <specialty>Web search and content analysis</specialty>
        <when_to_use>Need current web information or articles</when_to_use>
        <how_to_call>
          Use call_subagent tool with agent="web_researcher" and task="your query"
        </how_to_call>
      </agent>
    </sub_agents>
  </capabilities>

  <operational_status>
    <timestamp>2024-10-10T23:59:00Z</timestamp>
    <session_id>abc-123-def</session_id>
    <iterations_used>3/20</iterations_used>
    <actions_executed>7</actions_executed>
    <errors_encountered>2</errors_encountered>
  </operational_status>

  <context_feeds>
    <feed id="current_datetime">2024-10-10T23:59:00Z</feed>
    <feed id="research_session">
      {"active": true, "mode": "deep_research", "confidence": 0.85}
    </feed>
  </context_feeds>

  <recent_actions>
    <action id="search_1" status="success" iteration="2">
      Tool: web_search, Result: Found 15 articles about quantum computing
    </action>
    <action id="cache_1" status="success" iteration="2">
      Relic: research_cache.store, Result: Cached 15 results
    </action>
  </recent_actions>
</agent_cockpit>
```

### 2. Tool Examples in Context

Instead of just tool schemas, include working examples:

```xml
<tool_examples>
  <example>
    <description>Search for information and cache it</description>
    <thought>I need to research quantum computing and save the results</thought>
    <actions>
      <action type="tool" id="search1">
        {"name": "web_search", "parameters": {"query": "quantum computing 2024"}}
      </action>
      <action type="relic" id="cache1" depends_on="search1">
        {"name": "research_cache.store", "parameters": {"key": "quantum_2024", "data": "$search1"}}
      </action>
    </actions>
  </example>
</tool_examples>
```

### 3. JSON Format Enforcement

Add explicit JSON validation examples:

```xml
<critical_json_format>
  CORRECT ACTION FORMAT (COPY THIS EXACTLY):
  <action type="tool" id="my_action">
  {
    "name": "tool_name",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    }
  }
  </action>

  COMMON MISTAKES TO AVOID:
  ❌ DO NOT add comments in JSON (no // or /* */)
  ❌ DO NOT forget commas between properties
  ❌ DO NOT forget closing braces
  ❌ DO NOT use single quotes (use "double quotes")
  ❌ DO NOT add trailing commas

  VALIDATION CHECKLIST:
  ✓ Every opening { has a closing }
  ✓ Every opening [ has a closing ]
  ✓ All strings use "double quotes"
  ✓ Commas between properties (but not after last one)
  ✓ No comments anywhere in JSON
</critical_json_format>
```

## Code Changes Needed

### File: `src/agent/prompt.cpp`

Add new function:
```cpp
std::string Agent::buildAgentCockpit() const {
    std::stringstream cockpit;
    
    cockpit << "<agent_cockpit>\n";
    
    // 1. Identity section
    cockpit << "  <identity>\n";
    cockpit << "    <name>" << agentName << "</name>\n";
    cockpit << "    <description>" << agentDescription << "</description>\n";
    cockpit << "    <iteration_limit>" << iterationLimit << "</iteration_limit>\n";
    cockpit << "    <current_iteration>" << currentIteration << "</current_iteration>\n";
    
    // Add environment variables
    for (const auto& [key, value] : agentEnvVars) {
        cockpit << "    <env_var name=\"" << key << "\">" << value << "</env_var>\n";
    }
    cockpit << "  </identity>\n\n";
    
    // 2. Tools with detailed info
    cockpit << "  <tools_available>\n";
    for (const auto& [name, tool] : tools) {
        cockpit << "    <tool name=\"" << name << "\">\n";
        cockpit << "      <description>" << tool.description << "</description>\n";
        cockpit << "      <parameters>" << tool.parametersJson << "</parameters>\n";
        // Add example usage
        cockpit << "      <example>...</example>\n";
        cockpit << "    </tool>\n";
    }
    cockpit << "  </tools_available>\n\n";
    
    // 3. Relics with endpoints
    cockpit << "  <relics_available>\n";
    for (const auto& [name, relic] : relics) {
        cockpit << "    <relic name=\"" << name << "\">\n";
        cockpit << "      <type>" << relic->getServiceType() << "</type>\n";
        cockpit << "      <status>" << (relic->isRunning() ? "active" : "stopped") << "</status>\n";
        // Add endpoints
        for (const auto& endpoint : relic->getEndpoints()) {
            cockpit << "      <endpoint name=\"" << endpoint.name << "\" ";
            cockpit << "method=\"" << endpoint.method << "\" ";
            cockpit << "path=\"" << endpoint.path << "\"/>\n";
        }
        cockpit << "    </relic>\n";
    }
    cockpit << "  </relics_available>\n\n";
    
    // 4. Dynamic context (refreshed each iteration)
    cockpit << "  <current_state>\n";
    cockpit << "    <timestamp>" << getCurrentTimestamp() << "</timestamp>\n";
    cockpit << "    <iteration>" << currentIteration << "/" << iterationLimit << "</iteration>\n";
    
    // Execute context feeds and include
    for (const auto& [id, feed] : contextFeeds) {
        std::string feedContent = executeContextFeed(feed);
        cockpit << "    <context_feed id=\"" << id << "\">" << feedContent << "</context_feed>\n";
    }
    cockpit << "  </current_state>\n";
    
    cockpit << "</agent_cockpit>\n\n";
    
    return cockpit.str();
}
```

Then in `buildFullPrompt()`:
```cpp
std::string Agent::buildFullPrompt() const {
    std::stringstream promptSs;
    
    // 1. Identity
    promptSs << "<agent_identity>...</agent_identity>\n\n";
    
    // 2. System prompt
    promptSs << "<system_prompt>...</system_prompt>\n\n";
    
    // 3. AGENT COCKPIT (NEW!)
    promptSs << buildAgentCockpit();
    
    // 4. Streaming protocol
    if (streamingEnabled) {
        promptSs << buildStreamingProtocolInstructions();
    }
    
    // 5. Conversation history
    promptSs << buildConversationHistory();
    
    return promptSs.str();
}
```

## Benefits

**For the Agent:**
- Knows exactly what it can do
- Sees working examples
- Understands its current state
- Has clear JSON format guide
- Knows when to use each tool

**For Users:**
- Fewer errors (better JSON)
- Smarter tool usage
- Better sub-agent delegation
- More contextual responses

**For Debugging:**
- Can see what agent "knew" at each iteration
- Clear action history
- State tracking

## The "Cockpit" Metaphor

Think of it like a pilot's cockpit:
- **Instruments** = Tool statuses, relic health
- **Navigation** = Iteration counter, progress
- **Controls** = Available tools/actions
- **Mission briefing** = System prompt
- **Flight manual** = Tool examples, JSON format
- **Radio** = Context feeds, dynamic data

The agent needs to see ALL of this to make informed decisions!
