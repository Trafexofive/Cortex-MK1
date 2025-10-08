# Streaming Execution Protocol

## Overview

The **Streaming Execution Protocol** enables real-time action execution as the LLM generates its response. Actions are parsed and executed immediately when their closing tag is detected, without waiting for the complete response.

This provides:
- **Immediate feedback** - Users see thinking and actions in real-time
- **Parallel execution** - Independent actions start immediately
- **Better UX** - Progressive display instead of waiting for completion
- **Resource efficiency** - Start network/API calls while LLM is still generating

---

## Protocol Format

The LLM responds using XML-style tags with embedded JSON for action parameters:

```xml
<thought>
Your reasoning here. Streams to user in real-time as it's generated.
Can be multiple sentences explaining your approach and planning.
</thought>

<action type="tool" mode="async" id="fetch1">
{
  "name": "web_scraper",
  "parameters": {
    "url": "https://example.com"
  },
  "output_key": "webpage_data"
}
</action>

<action type="tool" mode="async" id="fetch2">
{
  "name": "database_query",
  "parameters": {
    "query": "SELECT * FROM users"
  },
  "output_key": "user_data"
}
</action>

THOUGHT{
    - content: 
}

<action type="agent" mode="sync" id="analyze">
{
  "name": "data_analyzer",
  "parameters": {
    "webpage": "$webpage_data",
    "users": "$user_data"
  },
  "depends_on": ["fetch1", "fetch2"],
  "output_key": "analysis"
}
</action>

<response>
Based on my analysis of the data:

**Key Findings:**
- Finding 1
- Finding 2

**Recommendations:**
1. Recommendation 1
2. Recommendation 2
</response>
```

---

## Tag Specifications

### `<thought>` Tag

**Purpose:** Stream the agent's reasoning process to the user in real-time.

**Behavior:**
- Content streams character-by-character as LLM generates it
- User sees thinking process live (like ChatGPT)
- Can include planning, reasoning, explanations
- Multiple `<thought>` blocks allowed

**Example:**
```xml
<thought>
I need to gather information from three sources:
1. Wikipedia for background
2. arXiv for recent research
3. News APIs for current developments

I'll fetch these in parallel since they're independent operations.
</thought>
```

### `<action>` Tag

**Purpose:** Define an action to execute (tool, agent, relic, workflow, llm).

**Attributes:**
- `type` - Action type: `tool`, `agent`, `relic`, `workflow`, `llm`
- `mode` - Execution mode: `sync`, `async`, `fire_and_forget`
- `id` - Unique identifier for the action (for dependencies)

**JSON Body:**
```json
{
  "name": "action_name",           // Required: Name of tool/agent/relic
  "parameters": {},                // Required: Input parameters
  "output_key": "var_name",        // Optional: Store result as $var_name
  "depends_on": ["id1", "id2"],    // Optional: Wait for these actions
  "timeout": 30,                   // Optional: Timeout in seconds
  "retry": 3                       // Optional: Retry count
}
```

**Behavior:**
- As soon as `</action>` is detected, parser extracts and validates JSON
- If `depends_on` is empty/null → execute immediately
- If `mode="async"` → run in background, continue parsing
- If `mode="sync"` → wait for completion before continuing
- If `mode="fire_and_forget"` → start execution, don't track result

**Example:**
```xml
<action type="tool" mode="async" id="fetch_data">
{
  "name": "web_scraper",
  "parameters": {
    "url": "https://api.example.com/data",
    "method": "GET"
  },
  "output_key": "api_data",
  "timeout": 30
}
</action>
```

### `<response>` Tag

**Purpose:** Final answer to the user (supports Markdown).

**Behavior:**
- Streams content as it's generated
- Can reference action outputs using `$variable_name`
- Supports full Markdown formatting
- Only one `<response>` block per agent turn

**Example:**
```xml
<response>
Based on the data from **$web_scraper**, here are the findings:

## Summary
The analysis shows...

## Details
1. Point 1
2. Point 2

**Next Steps:** ...
</response>
```

---

## Action Types

### 1. Tool (`type="tool"`)

Execute a stateless function/tool.

```xml
<action type="tool" mode="async" id="calc">
{
  "name": "calculator",
  "parameters": {
    "operation": "add",
    "a": 5,
    "b": 3
  },
  "output_key": "sum"
}
</action>
```

### 2. Agent (`type="agent"`)

Delegate to a sub-agent.

```xml
<action type="agent" mode="sync" id="analyze">
{
  "name": "data_analyzer",
  "parameters": {
    "data": "$fetched_data",
    "analysis_type": "comprehensive"
  },
  "output_key": "analysis_result"
}
</action>
```

### 3. Relic (`type="relic"`)

Call a persistent service (database, cache, API).

```xml
<action type="relic" mode="async" id="cache_store">
{
  "name": "redis_cache",
  "parameters": {
    "operation": "set",
    "key": "result_123",
    "value": "$computed_result",
    "ttl": 3600
  }
}
</action>
```

### 4. Workflow (`type="workflow"`)

Execute a multi-step workflow.

```xml
<action type="workflow" mode="sync" id="process">
{
  "name": "data_pipeline",
  "parameters": {
    "input_data": "$raw_data",
    "steps": ["validate", "transform", "load"]
  },
  "output_key": "processed_data"
}
</action>
```

### 5. LLM (`type="llm"`)

Make an LLM call (for sub-tasks, summarization, etc.).

```xml
<action type="llm" mode="async" id="summarize">
{
  "name": "summarize",
  "parameters": {
    "text": "$long_document",
    "max_length": 200,
    "model": "gemini-1.5-flash"
  },
  "output_key": "summary"
}
</action>
```

---

## Execution Modes

| Mode | Behavior | Use Case | Example |
|------|----------|----------|---------|
| **sync** ⏸️ | Wait for completion | Critical path, need result | Authentication, data analysis |
| **async** 🔄 | Run in background | Independent operations | Data fetching, API calls |
| **fire_and_forget** 🔥 | Don't wait for result | Logging, caching | Metrics, audit logs |

### Mode Examples

```xml
<!-- SYNC: Must wait for authentication -->
<action type="tool" mode="sync" id="auth">
{"name": "authenticate", "parameters": {"token": "$user_token"}}
</action>

<!-- ASYNC: Fetch data while continuing -->
<action type="tool" mode="async" id="fetch">
{"name": "fetch_data", "parameters": {"source": "api"}}
</action>

<!-- FIRE_AND_FORGET: Log but don't wait -->
<action type="relic" mode="fire_and_forget" id="log">
{"name": "logger", "parameters": {"event": "data_processed"}}
</action>
```

---

## Variable References

Use `$variable_name` to reference outputs from previous actions.

**Setting Output:**
```xml
<action type="tool" mode="async" id="fetch">
{
  "name": "web_scraper",
  "parameters": {"url": "https://example.com"},
  "output_key": "webpage"  ← Stores as $webpage
}
</action>
```

**Using Output:**
```xml
<action type="tool" mode="sync" id="analyze">
{
  "name": "text_analyzer",
  "parameters": {
    "text": "$webpage"  ← References previous output
  }
}
</action>
```

**In Response:**
```xml
<response>
The webpage at $webpage shows...  ← Can use in final response
</response>
```

---

## Dependencies

Actions can wait for other actions using `depends_on`:

```xml
<!-- Phase 1: Fetch data in parallel -->
<action type="tool" mode="async" id="fetch_wiki">
{"name": "web_scraper", "parameters": {"url": "wiki"}, "output_key": "wiki"}
</action>

<action type="tool" mode="async" id="fetch_news">
{"name": "web_scraper", "parameters": {"url": "news"}, "output_key": "news"}
</action>

<!-- Phase 2: Wait for both, then analyze -->
<action type="agent" mode="sync" id="analyze">
{
  "name": "data_analyzer",
  "parameters": {
    "wiki_data": "$wiki",
    "news_data": "$news"
  },
  "depends_on": ["fetch_wiki", "fetch_news"],  ← Waits for both
  "output_key": "analysis"
}
</action>

<!-- Phase 3: Cache the result (fire and forget) -->
<action type="relic" mode="fire_and_forget" id="cache">
{
  "name": "cache_store",
  "parameters": {"key": "analysis_result", "value": "$analysis"},
  "depends_on": ["analyze"]  ← Waits for analysis
}
</action>
```

---

## Streaming Behavior

### Real-Time Execution Timeline

```
Time 0s:  <thought> starts streaming
Time 0.5s: User sees: "Let me fetch data from..."
Time 1s:   User sees: "...Wikipedia and arXiv in parallel"
Time 1.5s: </thought> detected
Time 1.5s: <action id="fetch_wiki"> parsed → EXECUTES IMMEDIATELY
Time 1.6s: <action id="fetch_arxiv"> parsed → EXECUTES IMMEDIATELY (parallel)
Time 2s:   User sees: "🔄 Fetching from Wikipedia..."
Time 2.1s: User sees: "🔄 Fetching from arXiv..."
Time 3s:   fetch_wiki completes → $wiki_data available
Time 3.5s: fetch_arxiv completes → $arxiv_data available
Time 3.5s: <action id="analyze" depends_on=[...]> parsed
Time 3.5s: Dependencies met → analyze executes
Time 5s:   analyze completes → $analysis available
Time 5s:   <response> starts streaming
Time 5.5s: User sees: "Based on my analysis..."
```

### Key Points

1. **Thoughts stream immediately** - User sees reasoning as it's generated
2. **Actions execute as soon as parsed** - Don't wait for full response
3. **Parallel execution** - Independent async actions run simultaneously
4. **Dependencies respected** - Actions wait for `depends_on` to complete
5. **Response can use results** - Final answer references action outputs

---

## Complete Example

```xml
<thought>
I'll research this topic by:
1. Fetching Wikipedia article for background
2. Searching arXiv for recent papers
3. Getting latest news articles
4. Analyzing all sources together
5. Generating a comprehensive report
</thought>

<action type="tool" mode="async" id="wiki">
{
  "name": "web_scraper",
  "parameters": {"url": "https://en.wikipedia.org/wiki/AI"},
  "output_key": "wiki_data"
}
</action>

<action type="tool" mode="async" id="arxiv">
{
  "name": "arxiv_search",
  "parameters": {"query": "machine learning", "max_results": 10},
  "output_key": "papers"
}
</action>

<action type="tool" mode="async" id="news">
{
  "name": "news_api",
  "parameters": {"topic": "artificial intelligence", "days": 7},
  "output_key": "news_articles"
}
</action>

<action type="agent" mode="sync" id="analyze">
{
  "name": "comprehensive_analyzer",
  "parameters": {
    "wikipedia": "$wiki_data",
    "research_papers": "$papers",
    "news": "$news_articles"
  },
  "depends_on": ["wiki", "arxiv", "news"],
  "output_key": "comprehensive_analysis"
}
</action>

<action type="relic" mode="fire_and_forget" id="cache">
{
  "name": "results_cache",
  "parameters": {
    "key": "ai_research_report",
    "value": "$comprehensive_analysis",
    "ttl": 86400
  },
  "depends_on": ["analyze"]
}
</action>

<response>
# AI Research Report

## Overview
Based on analysis of Wikipedia, recent research papers, and news articles:

$comprehensive_analysis

## Key Trends
1. Transformer architectures dominate
2. Ethical AI gaining attention
3. Multi-modal models emerging

## Recommendations
- Focus on efficiency improvements
- Consider ethical implications
- Monitor regulatory developments
</response>
```

---

## Parser Implementation

The `StreamingProtocolParser` class handles:

1. **Token-by-token parsing** - Process LLM stream in real-time
2. **State machine** - Track parsing state (thought/action/response)
3. **Tag detection** - Identify opening/closing tags as they arrive
4. **Immediate execution** - Execute actions as soon as `</action>` is detected
5. **Dependency resolution** - Track which actions can execute now vs later

### Usage

```python
from streaming_protocol_parser import StreamingProtocolParser

async def llm_stream():
    # Your LLM streaming implementation
    async for token in llm.generate_stream(prompt):
        yield token

# Create parser with action executor
parser = StreamingProtocolParser(action_executor=execute_action)

# Parse and execute in real-time
async for event in parser.parse_stream(llm_stream()):
    if event.token_type == "thought":
        print(f"💭 {event.content}", end='', flush=True)
    
    elif event.token_type == "action":
        action = event.metadata['action']
        print(f"\n🎬 Executing: {action.name}")
    
    elif event.token_type == "response":
        print(f"\n{event.content}", end='', flush=True)
```

---

## Best Practices

### 1. Structure Your Thinking

```xml
✅ Good:
<thought>
I'll approach this in 3 steps:
1. Gather data from sources A and B
2. Analyze the combined dataset
3. Generate recommendations
</thought>

❌ Bad:
<thought>Um, let me think... maybe I should... yeah...</thought>
```

### 2. Use Parallel Actions

```xml
✅ Good: Parallel data fetching
<action type="tool" mode="async" id="fetch1">...</action>
<action type="tool" mode="async" id="fetch2">...</action>

❌ Bad: Sequential when could be parallel
<action type="tool" mode="sync" id="fetch1">...</action>
<action type="tool" mode="sync" id="fetch2">...</action>
```

### 3. Minimize Dependencies

```xml
✅ Good: Only depend on what you need
<action ... id="analyze" depends_on=["fetch_data"]>

❌ Bad: Unnecessary dependencies
<action ... id="analyze" depends_on=["fetch_data", "unrelated_action"]>
```

### 4. Use Appropriate Modes

```xml
✅ Good:
- sync for critical path (authentication, data needed immediately)
- async for parallel operations (multiple API calls)
- fire_and_forget for side effects (logging, caching)

❌ Bad:
- sync for everything (slow, sequential)
- async for dependent operations (race conditions)
```

---

## Error Handling

Actions should handle errors gracefully:

```json
{
  "name": "web_scraper",
  "parameters": {"url": "..."},
  "timeout": 30,
  "retry": 3,
  "on_error": "skip"  // or "fail", "retry"
}
```

If an action fails:
- Dependent actions are skipped
- Error is logged
- LLM can detect failure and adapt in `<response>`

---

## Future Enhancements

- [ ] **Conditional actions** - `<if>` tag for branching logic
- [ ] **Loops** - `<foreach>` for iterating over data
- [ ] **Parallel groups** - `<parallel>` tag for explicit parallelism
- [ ] **Rollback** - Undo actions on failure
- [ ] **Streaming action results** - Stream partial results as they're produced

---

*Streaming Execution Protocol v1.0 - Cortex-Prime MK1*
