# Streaming Execution Protocol

## First Draft - June 2024
- we need to add action execution inside thoughts directly (maybe even sub-thoughts, depending on would it actually improve usability).
    - might look like something like:
    ```
    <thought>
    I need to fetch data from source A.
    <action type="tool" mode="async" id="fetchA"> 
    {
      "name": "web_scraper",
      "parameters": {"url": "https://example.com"}
    }
    </action>
    While that runs, I can start planning the analysis.
    ```
    while this might look bit messy and useless at first, it actually allows the llm to interleave thinking and action execution more naturally, and also allows it to start actions earlier (without needing to wait for the full thought to finish). Also, not all actions need to be in thoughts, so the llm can still do normal actions outside of thoughts as well. Just like not all actions need to be in responses, or be shown to the user actually..

- we need to make the reponse block non terminating (without the final=true, the agent will keep looping. This is the way I do AI, if job is not done, just keep using COMPUTE. Optimizations here are: in getting the agent to do its job, that is the true way to save tokens, not fucking RAG), so that the agent can continue after giving a response. maybe something like:
    ```
    <response final="false">
    Here is what I found so far...
    </response>
    <thought>
    Now I will analyze this data further.
    </thought>
    ...
    <response final="true">
    Here is the final report...
    </response>
    ```

- We also need to give the llm a way to add its own context feeds:

```
context_feeds:
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      params: { format: "ISO8601", timezone: "UTC" }
      
  - id: "system_metrics"
    type: "periodic"
    interval: 30 # seconds
    source:
      type: "tool"
      name: "system_monitor_tool"
      params: { metrics: ["cpu", "memory"] }
  - id: "journal_tree"
    type: "on_demand"
    source:
      type: "tool"
      name: "filesystem"
      params: { path: "${JOURNAL_ROOT}", format: "tree" }
```
    - Will look like:
    ```
    <context_feed id="current_datetime">
    2024-06-15T12:34:56Z
    </context_feed>
    ```
    - These can be injected at the start of the prompt, or on-demand via an action
    - LLM will have access to these as $current_datetime, $system_metrics, etc.
    - This allows the LLM to get up-to-date context without needing to call an action
    - We can also have periodic feeds that update every N seconds, so the LLM always

- more context_feed types and features in the future:
    - periodic feeds that update every N seconds
    - internal feeds that call built-in functions (like system clock, random number, etc)
    - relic feeds that pull from persistent services (databases, caches, etc)
    - tool feeds that call external tools (APIs, web scraping, etc)
    - workflow feeds that run multi-step processes to gather context
    - llm feeds that summarize or transform existing context
    - feeds can have parameters to customize their behavior (e.g. time range for logs, filters for data, etc)
    - feeds can be enabled/disabled in the agent manifest to control what the LLM can access (for built in feeds, aka the actual prompt we build.)
    - feeds for auto injesting full repositories, documents, etc (like a full codebase, or a wiki dump, or a set of research papers)
    - feeds can be cached for a certain duration to avoid excessive calls (e.g. system metrics every 30 seconds, but cached for 5 minutes)
    - feeds can have size limits to avoid overwhelming the LLM (e.g. max 1k tokens)
    - The LLM will be able to add its own context feeds dynamically via an action:
         
    ```
    <action type="context_feed" mode="sync" id="add_feed">
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

    - This allows the LLM to request new context feeds as needed during execution
    - We will refer to these types of actions as "internal" in the future. they are essencially built-in actions in the agent object that the LLM can use to modify its own environment (of course, they can be disabled if needed, in the agent manifest).

---

## Implementation Status

### ✅ Currently Implemented
- Basic streaming protocol with `<thought>`, `<action>`, `<response>` tags
- Async/sync/fire-and-forget action execution modes
- Dependency resolution with `depends_on`
- Real-time action execution as tags are parsed
- Variable references with `$variable_name`
- Parallel execution of independent actions

### 🚧 In Development (June 2024 Draft)

#### 1. Actions Inside Thoughts
Allows LLM to interleave thinking and action execution more naturally. Actions can be embedded directly within `<thought>` blocks to start execution earlier without waiting for the full thought to complete.

**Benefits:**
- Earlier action execution (don't wait for thought to finish)
- Natural interleaving of reasoning and execution
- Actions can run while LLM continues thinking
- Not all actions need to be in thoughts or responses

#### 2. Non-Terminating Responses
Responses without `final="true"` allow the agent to continue execution after providing partial updates to the user.

**Benefits:**
- Progressive disclosure of results
- Agent can continue working after giving updates
- True compute-driven approach (keep looping until job is done)
- Better token efficiency by doing the work rather than RAG tricks

#### 3. Context Feeds
Dynamic context injection system that allows the LLM to access up-to-date information without explicit tool calls.

**Feed Types:**
- `on_demand` - Fetched when needed
- `periodic` - Auto-updates every N seconds
- `internal` - Built-in functions (clock, random, etc)
- `relic` - Persistent services (databases, caches)
- `tool` - External tools (APIs, web scraping)
- `workflow` - Multi-step processes
- `llm` - Summarization/transformation

**Features:**
- LLM can add its own feeds dynamically via internal actions
- Feeds can be cached to avoid excessive calls
- Size limits to avoid overwhelming context
- Enable/disable in agent manifest

---

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

## Advanced Features (June 2024 Draft)

### Actions Inside Thoughts

Actions can be embedded directly within `<thought>` blocks, allowing the LLM to start execution while still reasoning.

**Syntax:**
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

**Behavior:**
- Action executes immediately when `</action>` is detected
- LLM continues generating thought content
- User sees both reasoning and action execution in real-time
- Actions in thoughts don't block thought streaming

**Use Cases:**
- Start long-running operations early
- Interleave planning and execution
- Optimize for latency (parallel thinking + execution)
- More natural agent behavior

**Example:**
```xml
<thought>
To research this topic, I'll need multiple sources.

<action type="tool" mode="async" id="wiki">
{"name": "web_scraper", "parameters": {"url": "https://wikipedia.org/..."}}
</action>

While Wikipedia is loading, let me also fetch recent papers.

<action type="tool" mode="async" id="arxiv">
{"name": "arxiv_search", "parameters": {"query": "machine learning"}}
</action>

Now I'll wait for both and then analyze the combined results.
</thought>

<action type="agent" mode="sync" id="analyze">
{
  "name": "data_analyzer",
  "parameters": {"wiki": "$wiki", "papers": "$arxiv"},
  "depends_on": ["wiki", "arxiv"]
}
</action>
```

**Benefits:**
- **Earlier execution** - Actions start sooner, don't wait for thought to complete
- **Natural flow** - Reasoning and execution interleaved like human thought
- **Better UX** - User sees progress immediately
- **Flexibility** - Not all actions need to be in thoughts

---

### Non-Terminating Responses

Responses can be marked as non-final using `final="false"`, allowing the agent to continue execution after providing updates.

**Syntax:**
```xml
<response final="false">
Here is what I found so far...

## Preliminary Results
- Data fetched from 3 sources
- Initial analysis complete
- Still processing detailed insights
</response>

<thought>
Now I will analyze this data further and generate recommendations.
</thought>

<action type="agent" mode="sync" id="deep_analysis">
{
  "name": "deep_analyzer",
  "parameters": {"data": "$preliminary_data"}
}
</action>

<response final="true">
## Final Report

Based on comprehensive analysis:
...
</response>
```

**Behavior:**
- `final="false"` - Agent continues to next iteration
- `final="true"` - Agent terminates (default)
- Multiple partial responses allowed per execution
- Each response streams to user immediately

**Use Cases:**
- Long-running research tasks
- Multi-stage analysis
- Progressive disclosure of results
- Keep user informed during complex operations

**Philosophy:**
> "This is the way I do AI. If job is not done, just keep using COMPUTE. 
> Optimizations come from getting the agent to do its job, that is the true 
> way to save tokens, not fucking RAG."

**Example Execution Flow:**
```xml
<thought>
I'll research this in multiple phases.
</thought>

<action type="tool" mode="async" id="phase1">...</action>

<response final="false">
**Phase 1 Complete:** Found 15 relevant sources
</response>

<action type="agent" mode="sync" id="phase2">...</action>

<response final="false">
**Phase 2 Complete:** Analyzed patterns across sources
</response>

<action type="llm" mode="sync" id="phase3">...</action>

<response final="true">
**Final Report:** Here are the comprehensive findings...
</response>
```

---

### Context Feeds

Context feeds provide the LLM with dynamic, up-to-date information without explicit tool calls.

**Agent Manifest Configuration:**
```yaml
context_feeds:
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      params: 
        format: "ISO8601"
        timezone: "UTC"
      
  - id: "system_metrics"
    type: "periodic"
    interval: 30  # seconds
    source:
      type: "tool"
      name: "system_monitor_tool"
      params: 
        metrics: ["cpu", "memory"]
  
  - id: "journal_tree"
    type: "on_demand"
    source:
      type: "tool"
      name: "filesystem"
      params: 
        path: "${JOURNAL_ROOT}"
        format: "tree"
```

**Runtime Injection:**
```xml
<context_feed id="current_datetime">
2024-06-15T12:34:56Z
</context_feed>

<context_feed id="system_metrics">
{
  "cpu": 45.2,
  "memory": 62.8,
  "timestamp": "2024-06-15T12:34:56Z"
}
</context_feed>
```

**Accessing Feeds in Actions:**
```xml
<action type="tool" mode="sync" id="log_event">
{
  "name": "logger",
  "parameters": {
    "timestamp": "$current_datetime",
    "message": "Task completed",
    "system_load": "$system_metrics"
  }
}
</action>
```

**Feed Types:**

| Type | Trigger | Source | Example |
|------|---------|--------|---------|
| `on_demand` | When needed | Tool/Internal/Relic | Current time, file tree |
| `periodic` | Every N seconds | Tool/Relic | System metrics, logs |
| `internal` | Built-in | System functions | Clock, random, env vars |
| `relic` | Query service | Database/Cache/API | User data, config |
| `tool` | Execute tool | External script | Weather, stock prices |
| `workflow` | Multi-step | Pipeline | Aggregated data |
| `llm` | LLM call | Summarization | Condensed context |

**Advanced Features:**

1. **Caching:**
```yaml
- id: "expensive_data"
  type: "on_demand"
  cache_ttl: 300  # Cache for 5 minutes
  source:
    type: "tool"
    name: "expensive_api_call"
```

2. **Size Limits:**
```yaml
- id: "large_dataset"
  type: "on_demand"
  max_tokens: 1000  # Truncate if too large
  source:
    type: "relic"
    name: "data_warehouse"
```

3. **Conditional Loading:**
```yaml
- id: "debug_info"
  type: "on_demand"
  enabled: "${DEBUG_MODE}"  # Only load if debug enabled
  source:
    type: "internal"
    action: "debug_context"
```

---

### Internal Actions (Dynamic Feed Management)

The LLM can dynamically add context feeds during execution using internal actions.

**Adding a Feed:**
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
      "params": {
        "filter": "ERROR",
        "since": "1h"
      }
    }
  }
}
</action>
```

**Removing a Feed:**
```xml
<action type="internal" mode="sync" id="remove_feed">
{
  "name": "remove_context_feed",
  "parameters": {
    "id": "recent_errors"
  }
}
</action>
```

**Updating a Feed:**
```xml
<action type="internal" mode="sync" id="update_feed">
{
  "name": "update_context_feed",
  "parameters": {
    "id": "system_metrics",
    "interval": 60  # Change from 30s to 60s
  }
}
</action>
```

**Use Cases:**
- Add error logs when debugging
- Inject repository context for code tasks
- Load user preferences dynamically
- Adjust monitoring based on workload
- Clean up unused feeds to save tokens

**Security:**
Internal actions can be disabled in agent manifest:
```yaml
internal_actions:
  enabled: true
  allowed_actions:
    - "add_context_feed"
    - "remove_context_feed"
  # blocked_actions:
  #   - "update_context_feed"
```

---

### Context Feed Examples

**Example 1: Auto-Loading Repository Context**
```yaml
- id: "repo_structure"
  type: "on_demand"
  source:
    type: "tool"
    name: "git_tree"
    params:
      path: "${REPO_ROOT}"
      max_depth: 3
      
- id: "recent_commits"
  type: "on_demand"
  source:
    type: "tool"
    name: "git_log"
    params:
      count: 10
      format: "oneline"
```

**Example 2: Live System Monitoring**
```yaml
- id: "docker_status"
  type: "periodic"
  interval: 60
  source:
    type: "tool"
    name: "docker_ps"
    
- id: "service_health"
  type: "periodic"
  interval: 30
  source:
    type: "relic"
    name: "health_check_service"
```

**Example 3: Document Ingestion**
```yaml
- id: "project_docs"
  type: "on_demand"
  cache_ttl: 3600  # Cache for 1 hour
  max_tokens: 5000
  source:
    type: "workflow"
    name: "doc_aggregator"
    params:
      paths: ["docs/", "README.md"]
      format: "markdown"
```

**Example 4: LLM-Generated Context**
```yaml
- id: "code_summary"
  type: "on_demand"
  cache_ttl: 1800
  source:
    type: "llm"
    name: "summarize"
    params:
      prompt: "Summarize the main purpose of this codebase"
      context: "$repo_structure"
      model: "gemini-1.5-flash"
```

---

## Future Enhancements

- [ ] **Conditional actions** - `<if>` tag for branching logic
- [ ] **Loops** - `<foreach>` for iterating over data
- [ ] **Parallel groups** - `<parallel>` tag for explicit parallelism
- [ ] **Rollback** - Undo actions on failure
- [ ] **Streaming action results** - Stream partial results as they're produced
- [ ] **Sub-thoughts** - Nested thought blocks for hierarchical reasoning
- [ ] **Action templates** - Reusable action patterns
- [ ] **Feed transformations** - Transform feed data before injection
- [ ] **Cross-feed references** - Feeds that depend on other feeds
- [ ] **Distributed feeds** - Pull context from remote agents/services

---

*Streaming Execution Protocol v1.1 - Cortex-Prime MK1 (June 2024 Draft)*
