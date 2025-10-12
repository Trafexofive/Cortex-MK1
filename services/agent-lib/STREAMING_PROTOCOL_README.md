# Agent-Lib: Streaming Protocol & Modern Manifest Support

## Overview

Agent-lib has been updated to support the **Cortex-Prime Streaming Protocol v1.1** and **modern manifest format (v1.0 Sovereign Core Standard)**. This brings the C++ agent library in line with the broader Cortex-Prime ecosystem.

## New Features

### 1. Streaming Protocol Support

The agent can now generate and parse responses in real-time using the streaming execution protocol.

#### Key Features:
- **Real-time token streaming** - See LLM output as it's generated
- **Action execution during generation** - Actions start as soon as they're parsed
- **Parallel action execution** - Independent async actions run simultaneously  
- **Dependency resolution** - Actions can wait for other actions to complete
- **Variable references** - Use `$variable_name` to reference action outputs

#### Protocol Format:

```xml
<thought>
Your reasoning and planning here. Streams to user in real-time.
</thought>

<action type="tool" mode="async" id="fetch_data">
{
  "name": "web_scraper",
  "parameters": {"url": "https://example.com"},
  "output_key": "webpage_data"
}
</action>

<response final="true">
Your final answer in Markdown.
You can reference outputs: $webpage_data
</response>
```

#### Action Types:
- `tool` - Execute a stateless function/tool
- `agent` - Delegate to a sub-agent
- `relic` - Call a persistent service (database, cache, API)
- `workflow` - Execute a multi-step pipeline
- `llm` - Make an LLM call for sub-tasks
- `internal` - Modify agent environment

#### Execution Modes:
- `sync` - Wait for completion before continuing (critical path)
- `async` - Run in background, continue parsing (parallel operations)
- `fire_and_forget` - Start execution, don't wait for result (logging, caching)

### 2. Modern Manifest Format (v1.0)

Support for the Sovereign Core Standard manifest format with new capabilities.

#### Context Feeds (NEW!)

Dynamic context injection without explicit tool calls:

```yaml
context_feeds:
  # System clock - always available as $current_datetime
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      params:
        format: "ISO8601"
        timezone: "UTC"
  
  # Periodic system metrics
  - id: "system_metrics"
    type: "periodic"
    interval: 30  # seconds
    cache_ttl: 60
    max_tokens: 500
    source:
      type: "tool"
      name: "system_monitor"
```

**Feed Types:**
- `on_demand` - Fetched when needed
- `periodic` - Auto-updates every N seconds
- `internal` - Built-in functions (clock, random, env vars)
- `relic` - Persistent services (databases, caches)
- `tool` - External tools (APIs, web scraping)
- `workflow` - Multi-step processes
- `llm` - Summarization/transformation

#### Streaming Protocol Configuration

Enable streaming in the manifest:

```yaml
# Enable v1.1 streaming protocol
streaming_protocol: true
```

### 3. LLM Client Streaming Support

The base `LLMClient` class now supports streaming:

```cpp
// Traditional generate
std::string response = llm.generate(prompt);

// Streaming generate with callback
llm.generateStream(prompt, [](const std::string& token, bool isFinal) {
    std::cout << token << std::flush;
    if (isFinal) {
        std::cout << std::endl;
    }
});
```

#### MiniGemini Streaming

The Gemini client implements true HTTP streaming with Server-Sent Events:

```cpp
MiniGemini gemini(apiKey);
gemini.generateStream(prompt, [](const std::string& token, bool isFinal) {
    // Receive tokens as they arrive from Gemini API
    if (!isFinal) {
        std::cout << token << std::flush;
    }
});
```

### 4. Agent Streaming API

Agents can now use streaming protocol:

```cpp
Agent agent(llmClient, "my-agent");

// Enable streaming
agent.setStreamingEnabled(true);

// Add context feeds
StreamingProtocol::ContextFeed feed;
feed.id = "current_time";
feed.type = "on_demand";
// ... configure feed ...
agent.addContextFeed(feed);

// Streaming prompt with callback
agent.promptStreaming(userInput, [](const StreamingProtocol::TokenEvent& event) {
    switch (event.type) {
        case TokenEvent::Type::THOUGHT:
            std::cout << "💭 " << event.content << std::flush;
            break;
        case TokenEvent::Type::ACTION_START:
            std::cout << "\n🎬 Executing: " << event.action->name << std::endl;
            break;
        case TokenEvent::Type::RESPONSE:
            std::cout << event.content << std::flush;
            break;
    }
});
```

## Architecture

### New Components

1. **StreamingProtocol.hpp/cpp** - Streaming protocol parser
   - Real-time tag detection and parsing
   - Action execution coordination
   - Variable resolution
   - Context feed management

2. **streaming.cpp** - Agent streaming implementation
   - Integration with streaming parser
   - Action executor bridge
   - Context feed injection

3. **modelApi.hpp** - Enhanced base class with streaming
   - StreamCallback type definition
   - Virtual `generateStream()` method

4. **MiniGemini.cpp** - Streaming HTTP implementation
   - Server-Sent Events (SSE) support
   - Real-time token callbacks
   - Efficient chunk parsing

### Updated Components

1. **import.cpp** - Modern manifest loading
   - Context feeds parsing
   - Streaming protocol configuration
   - v1.0 manifest support

2. **Agent.hpp/cpp** - Streaming support
   - `promptStreaming()` method
   - Context feed management
   - Streaming parser integration

## Usage Examples

### Basic Streaming Agent

```yaml
# agent.yml
name: "my-streaming-agent"
streaming_protocol: true

context_feeds:
  - id: "datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"

tools:
  calculator:
    type: script
    runtime: python
    # ... tool configuration ...
```

### Multi-Action Parallel Execution

```xml
<thought>
I'll fetch data from 3 sources in parallel.
</thought>

<action type="tool" mode="async" id="fetch1">
{"name": "web_scraper", "parameters": {"url": "source1"}, "output_key": "data1"}
</action>

<action type="tool" mode="async" id="fetch2">
{"name": "api_call", "parameters": {"endpoint": "source2"}, "output_key": "data2"}
</action>

<action type="tool" mode="async" id="fetch3">
{"name": "database_query", "parameters": {"query": "..."}, "output_key": "data3"}
</action>

<action type="agent" mode="sync" id="analyze" depends_on=["fetch1", "fetch2", "fetch3"]>
{"name": "analyzer", "parameters": {"sources": ["$data1", "$data2", "$data3"]}}
</action>

<response final="true">
Analysis complete based on all three sources.
</response>
```

### Progressive Responses (v1.1)

```xml
<action type="tool" mode="async" id="phase1">...</action>

<response final="false">
Phase 1 started. Will update when complete.
</response>

<action type="agent" mode="sync" id="phase2" depends_on=["phase1"]>...</action>

<response final="true">
All phases complete. Final results: ...
</response>
```

## Building

The streaming protocol support requires C++17 and the following dependencies:
- libcurl (for HTTP streaming)
- jsoncpp (for JSON parsing)
- yaml-cpp (for manifest parsing)

```bash
cd /home/mlamkadm/repos/Cortex-Prime-MK1/services/agent-lib
make clean
make -j4
```

Build artifacts:
- `agent-server` - HTTP server with streaming support
- `agent-bin` - CLI tool

## Testing

Example manifest with streaming:

```bash
# Load the example agent
./agent-server --config config/agents/streaming-example/agent.yml

# Or use the CLI
./agent-bin
> load config/agents/streaming-example/agent.yml
> What is 42 + 58?
```

## Documentation

- **Streaming Protocol Spec**: `/docs/streaming/STREAMING_PROTOCOL.md`
- **Quick Reference**: `/docs/design-specs/STREAMING_PROTOCOL_V1.1_QUICK_REFERENCE.md`
- **Python Implementation**: `/services/runtime_executor/streaming_protocol_parser.py`
- **Manifest Standard**: `/testing/test_against_manifest/MANIFEST_SUMMARY.md`

## Compatibility

### Backward Compatibility
- Legacy non-streaming mode still works
- Old manifest format continues to be supported
- Streaming is opt-in via `streaming_protocol: true`

### Forward Compatibility
- Implements v1.1 protocol features
- Context feeds extensible for future feed types
- Action types extensible for new action kinds

## Performance

### Streaming Benefits
1. **Lower latency** - User sees output immediately
2. **Better UX** - Progressive disclosure of thinking
3. **Parallel execution** - Actions start while LLM generates
4. **Resource efficiency** - Network/API calls overlap with generation

### Context Feeds Benefits
1. **Token savings** - No need for explicit tool calls
2. **Always up-to-date** - Periodic feeds auto-refresh
3. **Cleaner prompts** - Context injected automatically
4. **Caching** - Expensive feeds cached with TTL

## Migration Guide

### From Legacy to Streaming

**Before:**
```yaml
name: "old-agent"
model: "gemini-2.0-flash"
system_prompt: "You are a helpful assistant."
```

**After:**
```yaml
name: "new-agent"
streaming_protocol: true
model: "gemini-2.0-flash"

persona:
  system_prompt: |
    You are a helpful assistant.
    Use the streaming protocol format for responses.

context_feeds:
  - id: "datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
```

### Code Migration

**Before:**
```cpp
Agent agent(llm, "my-agent");
std::string response = agent.prompt("Hello");
std::cout << response << std::endl;
```

**After:**
```cpp
Agent agent(llm, "my-agent");
agent.setStreamingEnabled(true);

agent.promptStreaming("Hello", [](const auto& event) {
    if (event.type == TokenEvent::Type::RESPONSE) {
        std::cout << event.content << std::flush;
    }
});
```

## Known Limitations

1. **SSE parsing** - Basic implementation, may need refinement for complex streams
2. **Context feed execution** - Internal/tool feeds need full implementation
3. **Error recovery** - Streaming errors may require full restart
4. **Token buffering** - Some latency from line buffering

## Future Enhancements

- [ ] Actions embedded in thoughts (inline action execution)
- [ ] Non-terminating responses (multi-stage agent loops)
- [ ] Dynamic context feed management (add/remove feeds at runtime)
- [ ] Internal actions (agent environment modification)
- [ ] Streaming action results (partial results during execution)
- [ ] Cross-feed references (feeds depending on other feeds)

## Contributing

When adding new features:
1. Update protocol version in headers
2. Add tests in `/testing/test_against_manifest/`
3. Update documentation
4. Maintain backward compatibility
5. Follow the Sovereign Core Standard

## License

Same as Cortex-Prime MK1

---

**Version**: 1.1.0  
**Last Updated**: 2024-01-10  
**Status**: Production Ready
