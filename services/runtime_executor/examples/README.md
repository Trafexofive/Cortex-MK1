# Streaming Execution Protocol v1.1 - Examples

This directory contains examples demonstrating the advanced features added in the June 2024 draft of the Streaming Execution Protocol.

## New Features

### 1. Actions Inside Thoughts

Actions can now be embedded directly within `<thought>` blocks, allowing the LLM to start execution while still reasoning.

**Benefits:**
- Earlier action execution (don't wait for thought to complete)
- Natural interleaving of reasoning and execution
- Actions run in background while LLM continues thinking
- More efficient use of latency

**Example:**
```xml
<thought>
I need to fetch data from source A.
<action type="tool" mode="async" id="fetchA"> 
{
  "name": "web_scraper",
  "parameters": {"url": "https://example.com"}
}
</action>
While that runs, I can start planning the analysis.
</thought>
```

### 2. Non-Terminating Responses

Responses without `final="true"` allow the agent to continue execution after providing partial updates.

**Benefits:**
- Progressive disclosure of results
- Agent continues working after giving updates
- True compute-driven approach (keep looping until done)
- Better user experience with incremental feedback

**Example:**
```xml
<response final="false">
Here is what I found so far...
</response>

<thought>
Now I will analyze this data further.
</thought>

<response final="true">
Here is the final report...
</response>
```

### 3. Context Feeds

Dynamic context injection system that provides the LLM with up-to-date information without explicit tool calls.

**Feed Types:**
- `on_demand` - Fetched when needed
- `periodic` - Auto-updates every N seconds
- `internal` - Built-in functions (clock, random, etc)
- `relic` - Persistent services (databases, caches)
- `tool` - External tools (APIs, web scraping)
- `workflow` - Multi-step processes
- `llm` - Summarization/transformation

**Features:**
- Caching to avoid excessive calls
- Size limits to avoid overwhelming context
- Enable/disable in agent manifest
- LLM can add feeds dynamically

**Example Agent Manifest:**
```yaml
context_feeds:
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      params: { format: "ISO8601", timezone: "UTC" }
      
  - id: "system_metrics"
    type: "periodic"
    interval: 30
    source:
      type: "tool"
      name: "system_monitor_tool"
      params: { metrics: ["cpu", "memory"] }
```

**Runtime Injection:**
```xml
<context_feed id="current_datetime">
2024-06-15T12:34:56Z
</context_feed>

<context_feed id="system_metrics">
{"cpu": 45.2, "memory": 62.8}
</context_feed>
```

### 4. Internal Actions

The LLM can dynamically modify its own execution environment using internal actions.

**Available Internal Actions:**
- `add_context_feed` - Add a new context feed
- `remove_context_feed` - Remove an existing feed
- `update_context_feed` - Modify feed parameters
- `list_context_feeds` - List all active feeds
- `clear_context` - Clear execution context
- `set_variable` - Set a context variable
- `delete_variable` - Delete a context variable

**Example:**
```xml
<action type="internal" mode="sync" id="add_feed">
{
  "name": "add_context_feed",
  "parameters": {
    "id": "recent_errors",
    "type": "on_demand",
    "source": {
      "type": "relic",
      "name": "log_service",
      "params": { "filter": "ERROR", "since": "1h" }
    }
  }
}
</action>
```

**Security:**
Internal actions can be controlled in the agent manifest:
```yaml
internal_actions:
  enabled: true
  allowed_actions:
    - "add_context_feed"
    - "remove_context_feed"
  # blocked_actions:
  #   - "update_context_feed"
```

## Files

- **streaming_protocol_v1_1_examples.py** - Complete examples of all new features

## Usage

Run the examples:
```bash
python streaming_protocol_v1_1_examples.py
```

This will display example snippets for each feature.

## Implementation Status

- ✅ Protocol specification updated in `/docs/STREAMING_PROTOCOL.md`
- ✅ Data models added in `/services/runtime_executor/models/agent_execution_protocol.py`
- ✅ Parser enhanced in `/services/runtime_executor/streaming_protocol_parser.py`
- 🚧 Executor integration (in progress)
- 🚧 Context feed manager (planned)
- 🚧 Internal action handlers (planned)

## Philosophy

The streaming execution protocol embraces a **compute-driven approach**:

> "If the job is not done, just keep using COMPUTE. Optimizations come from 
> getting the agent to do its job effectively, not from shortcuts like RAG."

This means:
- Agents loop until completion, not until token limit
- Partial responses keep users informed while work continues
- Context feeds provide fresh data without bloat
- Internal actions enable dynamic adaptation

## Next Steps

1. Implement context feed manager with caching
2. Add internal action handlers
3. Update agent loop executor to support non-terminating responses
4. Add tests for new parser features
5. Create example agents using these features

## Related Documentation

- [Streaming Protocol Documentation](/docs/STREAMING_PROTOCOL.md)
- [Agent Execution Protocol](/docs/AGENT_EXECUTION_PROTOCOL.md)
- [Repository Structure](/docs/REPOSITORY_STRUCTURE.md)
