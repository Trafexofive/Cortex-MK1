# Streaming Protocol v1.1 - Quick Reference

Quick reference for developers implementing or using the Streaming Execution Protocol v1.1.

## Basic Syntax

### Thought Block
```xml
<thought>
Your reasoning here. Streams in real-time.
</thought>
```

### Action Block
```xml
<action type="tool" mode="async" id="unique_id">
{
  "name": "tool_name",
  "parameters": {"key": "value"},
  "output_key": "variable_name",
  "depends_on": ["other_action_id"]
}
</action>
```

### Response Block
```xml
<response final="true">
Your answer to the user.
</response>
```

## New in v1.1

### 1. Actions Inside Thoughts
```xml
<thought>
I need data from source A.
<action type="tool" mode="async" id="fetch">
{"name": "scraper", "parameters": {"url": "..."}}
</action>
While that runs, I'll plan next steps.
</thought>
```

### 2. Non-Terminating Responses
```xml
<response final="false">
Here's what I found so far...
</response>

<thought>Continuing analysis...</thought>

<response final="true">
Final results.
</response>
```

### 3. Context Feeds
```xml
<!-- In agent manifest -->
context_feeds:
  - id: "datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"

<!-- At runtime -->
<context_feed id="datetime">
2024-06-15T12:34:56Z
</context_feed>

<!-- In actions -->
<action type="tool" mode="sync" id="log">
{"name": "logger", "parameters": {"timestamp": "$datetime"}}
</action>
```

### 4. Internal Actions
```xml
<action type="internal" mode="sync" id="add_feed">
{
  "name": "add_context_feed",
  "parameters": {
    "id": "errors",
    "type": "on_demand",
    "source": {
      "type": "relic",
      "name": "log_service",
      "params": {"filter": "ERROR"}
    }
  }
}
</action>
```

## Action Types

| Type | Description | Example |
|------|-------------|---------|
| `tool` | Stateless function | Web scraper, calculator |
| `agent` | Sub-agent delegation | Data analyzer agent |
| `relic` | Persistent service | Database, cache, API |
| `workflow` | Multi-step pipeline | ETL process |
| `llm` | LLM call | Summarization, generation |
| `internal` | Modify environment | Add context feed |

## Execution Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `sync` | Wait for completion | Critical path operations |
| `async` | Run in background | Parallel data fetching |
| `fire_and_forget` | Don't wait for result | Logging, caching |

## Context Feed Types

| Type | Trigger | Example |
|------|---------|---------|
| `on_demand` | When needed | Current time, file tree |
| `periodic` | Every N seconds | System metrics, health |
| `internal` | Built-in | System clock, random |
| `relic` | Service query | Database data, cache |
| `tool` | Tool execution | API call, web scrape |
| `workflow` | Pipeline | Aggregated data |
| `llm` | LLM call | Summarization |

## Internal Action Types

| Action | Purpose |
|--------|---------|
| `add_context_feed` | Add new feed |
| `remove_context_feed` | Remove feed |
| `update_context_feed` | Modify feed |
| `list_context_feeds` | List active feeds |
| `clear_context` | Clear execution context |
| `set_variable` | Set context variable |
| `delete_variable` | Delete variable |

## Variable References

Use `$variable_name` to reference:
- Action outputs (via `output_key`)
- Context feed values
- Execution context variables

```xml
<action type="tool" mode="async" id="fetch">
{"name": "scraper", "output_key": "data"}
</action>

<action type="agent" mode="sync" id="analyze">
{"name": "analyzer", "parameters": {"input": "$data"}}
</action>

<response final="true">
Results: $data
</response>
```

## Dependencies

Actions can wait for others:
```xml
<!-- Phase 1: Parallel fetch -->
<action ... id="fetch_A">...</action>
<action ... id="fetch_B">...</action>

<!-- Phase 2: Wait for both -->
<action ... id="analyze" depends_on=["fetch_A", "fetch_B"]>
...
</action>
```

## Agent Manifest Configuration

### Enable Context Feeds
```yaml
context_feeds:
  - id: "system_clock"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      params: { format: "ISO8601" }
      
  - id: "metrics"
    type: "periodic"
    interval: 30
    cache_ttl: 300
    max_tokens: 500
    source:
      type: "tool"
      name: "system_monitor"
```

### Control Internal Actions
```yaml
internal_actions:
  enabled: true
  allowed_actions:
    - "add_context_feed"
    - "remove_context_feed"
  blocked_actions:
    - "clear_context"
```

## Common Patterns

### Pattern 1: Parallel Data Fetch + Analysis
```xml
<thought>
Fetching from multiple sources in parallel.
<action type="tool" mode="async" id="src1">
{"name": "scraper", "parameters": {"url": "..."}, "output_key": "data1"}
</action>
<action type="tool" mode="async" id="src2">
{"name": "api_call", "parameters": {"endpoint": "..."}, "output_key": "data2"}
</action>
</thought>

<action type="agent" mode="sync" id="analyze" depends_on=["src1", "src2"]>
{"name": "analyzer", "parameters": {"d1": "$data1", "d2": "$data2"}}
</action>
```

### Pattern 2: Progressive Updates
```xml
<action type="workflow" mode="async" id="phase1">...</action>

<response final="false">
Phase 1 started. Will update when complete.
</response>

<action type="agent" mode="sync" id="phase2" depends_on=["phase1"]>
...
</action>

<response final="true">
All phases complete. Results: ...
</response>
```

### Pattern 3: Dynamic Context Adaptation
```xml
<thought>
Need error monitoring. Adding context feed.
</thought>

<action type="internal" mode="sync" id="add_monitoring">
{
  "name": "add_context_feed",
  "parameters": {
    "id": "errors",
    "type": "periodic",
    "interval": 10,
    "source": {"type": "relic", "name": "log_service"}
  }
}
</action>

<thought>
Now I have $errors available. Monitoring active.
</thought>
```

### Pattern 4: Conditional Execution
```xml
<action type="tool" mode="sync" id="check">
{"name": "status_check", "output_key": "status"}
</action>

<thought>
Status is $status. Will proceed based on result.
</thought>

<!-- If status good, continue -->
<action type="workflow" mode="sync" id="main">
{"name": "main_workflow"}
</action>

<!-- If status bad, debug -->
<action type="internal" mode="sync" id="debug_feed">
{"name": "add_context_feed", "parameters": {"id": "debug", ...}}
</action>
```

## Error Handling

### Action-Level
```json
{
  "name": "risky_operation",
  "timeout": 30,
  "retry_count": 3,
  "retry_delay_seconds": 5,
  "skip_on_error": true
}
```

### Response-Level
```xml
<response final="false">
Encountered error in phase 1. Attempting recovery...
</response>

<action type="internal" mode="sync" id="add_logs">
{"name": "add_context_feed", "parameters": {"id": "error_logs", ...}}
</action>

<response final="true">
Recovery successful. Operation complete.
</response>
```

## Best Practices

1. **Use async for independent operations**
   - Parallel data fetching
   - Non-blocking API calls

2. **Use sync for critical path**
   - Authentication
   - Data that's immediately needed

3. **Use fire_and_forget for side effects**
   - Logging
   - Caching
   - Metrics

4. **Embed actions in thoughts for better latency**
   - Start long operations early
   - Continue thinking while they run

5. **Use partial responses for long tasks**
   - Keep users informed
   - Progressive disclosure

6. **Add context feeds for frequently needed data**
   - Current time
   - System status
   - Configuration

7. **Clean up temporary feeds**
   - Use `remove_context_feed` when done
   - Prevent context bloat

## Performance Tips

- Cache periodic feeds with appropriate TTL
- Set size limits on feeds to avoid bloat
- Use `fire_and_forget` for non-critical operations
- Minimize dependencies to maximize parallelism
- Start actions early with actions-in-thoughts

## Security Checklist

- [ ] Whitelist allowed internal actions
- [ ] Validate context feed sources
- [ ] Set max iteration limits
- [ ] Monitor compute usage
- [ ] Audit sensitive operations
- [ ] Enforce size limits on feeds
- [ ] Rate limit periodic feeds

## Examples

See `/services/runtime_executor/examples/` for complete examples:
- `streaming_protocol_v1_1_examples.py` - All features
- `README.md` - Usage guide

## Documentation

- [Full Protocol Spec](/docs/STREAMING_PROTOCOL.md)
- [Implementation Summary](/docs/STREAMING_PROTOCOL_V1.1_IMPLEMENTATION_SUMMARY.md)
- [Agent Execution Protocol](/docs/AGENT_EXECUTION_PROTOCOL.md)
