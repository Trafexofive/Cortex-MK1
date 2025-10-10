# Agent Execution Protocol v2.0

## Stream-As-We-Execute Model

The new agent execution protocol introduces a modern, streaming-first approach to agent loops with async/sync action orchestration, dependency resolution, and real-time progress updates.

---

## Core Concepts

### 1. Actions

An **Action** is a single executable unit in the agent's plan. Actions can be:

- **Tools** - Execute stateless functions
- **Agents** - Delegate to sub-agents  
- **Relics** - Call persistent services (databases, caches, APIs)
- **Workflows** - Execute multi-step pipelines
- **LLM** - Make LLM calls for reasoning
- **Decision** - Conditional branching logic

### 2. Execution Modes

Each action has an execution mode:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **SYNC** | Wait for completion before continuing | Critical path operations, must have result |
| **ASYNC** | Execute and continue, collect result later | Parallel data fetching, independent operations |
| **FIRE_AND_FORGET** | Execute and don't wait for result | Logging, caching, non-critical operations |

### 3. Dependency Resolution

Actions can depend on other actions using `depends_on` field:

```python
Action(
    name="analyze_data",
    depends_on=["fetch_source_1", "fetch_source_2"],  # Wait for both
    wait_for_all=True  # or False to wait for just one
)
```

The executor builds a **Directed Acyclic Graph (DAG)** and executes actions in dependency order, maximizing parallelism.

### 4. Streaming Execution

The executor streams events in real-time as execution progresses:

```python
async for event in executor.execute_agent_loop():
    if event.event_type == "action_completed":
        print(f"Action {event.action_name} completed!")
        print(f"Output: {event.data['output']}")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Loop Executor                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Iteration Loop (up to max_iterations)      │    │
│  │                                                     │    │
│  │  1. Generate Execution Plan (via LLM)             │    │
│  │     ├─ Analyze current context                    │    │
│  │     ├─ Review previous results                    │    │
│  │     └─ Create Action list with dependencies       │    │
│  │                                                     │    │
│  │  2. Build Execution Graph (DAG)                   │    │
│  │     ├─ Validate no circular dependencies          │    │
│  │     └─ Determine execution order                  │    │
│  │                                                     │    │
│  │  3. Execute Actions (Streaming)                   │    │
│  │     ├─ Wave-based execution                       │    │
│  │     ├─ Respect dependencies                       │    │
│  │     ├─ Parallel execution (up to max_parallel)   │    │
│  │     ├─ Stream results as they complete           │    │
│  │     └─ Update context with outputs               │    │
│  │                                                     │    │
│  │  4. Check Termination Conditions                  │    │
│  │     ├─ Goal achieved?                             │    │
│  │     ├─ Max iterations reached?                    │    │
│  │     ├─ No progress?                               │    │
│  │     └─ User requested stop?                       │    │
│  │                                                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Stream Events: ───────────────────────────────────────>    │
│    • agent_started                                          │
│    • iteration_started                                      │
│    • plan_generated                                         │
│    • action_started                                         │
│    • action_completed / action_failed                       │
│    • iteration_completed                                    │
│    • agent_completed                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Execution Model

### Wave-Based Parallel Execution

Actions are executed in "waves" based on their dependencies:

**Example Plan:**
```python
actions = [
    Action("fetch_wiki", depends_on=[], mode=ASYNC),
    Action("fetch_arxiv", depends_on=[], mode=ASYNC),
    Action("analyze", depends_on=["fetch_wiki", "fetch_arxiv"], mode=SYNC),
    Action("cache_result", depends_on=["analyze"], mode=FIRE_AND_FORGET),
    Action("quality_check", depends_on=["analyze"], mode=ASYNC)
]
```

**Execution Timeline:**
```
Wave 1 (parallel):
  ├─ fetch_wiki (async)      ──┐
  └─ fetch_arxiv (async)     ──┤
                               │
Wave 2 (after wave 1):         ├─> analyze (sync)
                               │
Wave 3 (parallel after wave 2):
  ├─ cache_result (fire_and_forget)
  └─ quality_check (async)
```

### Context Management

Actions can store outputs in the shared execution context:

```python
Action(
    name="fetch_data",
    output_key="wiki_data",  # Store result here
    ...
)

Action(
    name="analyze",
    parameters={
        "data": "$wiki_data"  # Reference from context ($ prefix)
    },
    ...
)
```

The context is persistent across iterations and accessible to all actions.

---

## Event Types

### Agent Lifecycle Events

| Event Type | When | Data |
|------------|------|------|
| `agent_started` | Agent execution begins | execution_id, agent_name, max_iterations |
| `agent_completed` | Agent finished successfully | total_iterations, total_actions, metrics |
| `agent_failed` | Agent failed with error | error, error_type |

### Iteration Events

| Event Type | When | Data |
|------------|------|------|
| `iteration_started` | New iteration begins | iteration, max_iterations |
| `plan_generated` | LLM generated execution plan | actions_count, actions list |
| `iteration_completed` | Iteration finished | iteration, actions_completed |

### Action Events

| Event Type | When | Data |
|------------|------|------|
| `action_started` | Action execution begins | action_id, action_name, type, mode, target, parameters |
| `action_completed` | Action finished successfully | status, duration_seconds, output |
| `action_failed` | Action failed | error, error_type |

### Special Events

| Event Type | When | Data |
|------------|------|------|
| `llm_token` | LLM generates token (streaming) | token, cumulative_tokens |
| `termination` | Agent loop terminating | reason |
| `warning` | Warning condition | message |
| `error` | Error occurred | error, error_type |

---

## Usage Examples

### Example 1: Research Agent

```python
from models.agent_execution_protocol import (
    Action, ActionType, ActionMode, ExecutionPlan
)

# Create execution plan
plan = ExecutionPlan(
    agent_name="research_agent",
    iteration=1,
    max_parallel=3,
    actions=[
        # Fetch data from multiple sources in parallel
        Action(
            name="fetch_wikipedia",
            type=ActionType.TOOL,
            mode=ActionMode.ASYNC,
            target="web_scraper",
            parameters={"url": "https://en.wikipedia.org/wiki/AI"},
            output_key="wiki_data"
        ),
        Action(
            name="fetch_arxiv",
            type=ActionType.TOOL,
            mode=ActionMode.ASYNC,
            target="arxiv_search",
            parameters={"query": "artificial intelligence"},
            output_key="arxiv_data"
        ),
        
        # Analyze combined results (waits for both fetches)
        Action(
            name="analyze_data",
            type=ActionType.AGENT,
            mode=ActionMode.SYNC,
            target="data_analyzer",
            depends_on=["fetch_wikipedia", "fetch_arxiv"],
            parameters={
                "wiki": "$wiki_data",
                "papers": "$arxiv_data"
            },
            output_key="analysis"
        ),
        
        # Cache result (don't wait)
        Action(
            name="cache_result",
            type=ActionType.RELIC,
            mode=ActionMode.FIRE_AND_FORGET,
            target="results_cache",
            depends_on=["analyze_data"],
            parameters={
                "key": "ai_research",
                "value": "$analysis",
                "ttl": 3600
            }
        )
    ]
)
```

### Example 2: Streaming Execution

```python
from agent_loop_executor import AgentLoopExecutor
from models.agent_execution_protocol import AgentLoopProtocol

# Configure protocol
protocol = AgentLoopProtocol(
    mode="autonomous",
    max_iterations=10,
    stream_action_results=True,
    stream_llm_tokens=True,
    allow_parallel_actions=True,
    max_parallel_actions=5
)

# Create executor
executor = AgentLoopExecutor(
    agent_name="my_agent",
    protocol=protocol,
    tool_executor=tool_exec,
    llm_client=llm_client
)

# Execute with real-time streaming
async for event in executor.execute_agent_loop():
    if event.event_type == "action_started":
        print(f"▶ Starting: {event.action_name}")
    
    elif event.event_type == "action_completed":
        print(f"✅ Completed: {event.action_name}")
        print(f"   Output: {event.data['output']}")
    
    elif event.event_type == "action_failed":
        print(f"❌ Failed: {event.action_name}")
        print(f"   Error: {event.data['error']}")
    
    elif event.event_type == "llm_token":
        print(event.data['token'], end='', flush=True)
    
    elif event.event_type == "plan_generated":
        print(f"\n📋 Plan: {event.data['actions_count']} actions")
```

### Example 3: Complex Dependencies

```python
# Create a complex DAG
actions = [
    # Parallel data fetching
    Action("fetch_A", depends_on=[], mode=ASYNC),
    Action("fetch_B", depends_on=[], mode=ASYNC),
    Action("fetch_C", depends_on=[], mode=ASYNC),
    
    # Process A and B together
    Action("process_AB", depends_on=["fetch_A", "fetch_B"], mode=SYNC),
    
    # Process C separately
    Action("process_C", depends_on=["fetch_C"], mode=SYNC),
    
    # Combine all results
    Action(
        "combine_all",
        depends_on=["process_AB", "process_C"],
        wait_for_all=True,  # Must wait for both
        mode=SYNC
    ),
    
    # Final steps in parallel
    Action("save_result", depends_on=["combine_all"], mode=ASYNC),
    Action("notify_user", depends_on=["combine_all"], mode=ASYNC)
]
```

---

## Configuration

### AgentLoopProtocol Options

```python
protocol = AgentLoopProtocol(
    # Loop control
    mode="autonomous",  # strict, default, or autonomous
    max_iterations=10,
    max_execution_time_seconds=3600,
    
    # Streaming
    stream_llm_tokens=True,
    stream_action_results=True,
    stream_thoughts=True,
    
    # Execution
    allow_parallel_actions=True,
    max_parallel_actions=5,
    auto_retry_on_failure=True,
    
    # Decision making
    require_user_approval=False,
    auto_plan_next_iteration=True,
    
    # Termination
    terminate_on_goal_achieved=True,
    terminate_on_no_progress=True,
    terminate_on_error=False
)
```

---

## Key Features

### ✅ Parallel Execution
Actions without dependencies execute in parallel up to `max_parallel` limit.

### ✅ Dependency Resolution
Automatic DAG construction and wave-based execution ensures correct ordering.

### ✅ Streaming Results
Get real-time updates as actions complete, don't wait for entire iteration.

### ✅ Context Persistence
Shared context across all actions and iterations for data flow.

### ✅ Error Handling
Per-action error handling with `skip_on_error`, retry policies, and fail-fast support.

### ✅ Resource Control
Timeout per action, max parallel actions, resource limits.

### ✅ Flexible Modes
SYNC for critical path, ASYNC for parallel work, FIRE_AND_FORGET for side effects.

---

## Migration from v1.0

### Old Model (Sequential)
```python
# v1.0 - Sequential execution
for iteration in range(max_iterations):
    # LLM decides next action
    action = llm.decide_next_action(context)
    
    # Execute and wait
    result = execute_action(action)
    
    # Update context
    context.update(result)
```

### New Model (Streaming + Parallel)
```python
# v2.0 - Streaming with parallel execution
async for event in executor.execute_agent_loop():
    # Get real-time updates
    if event.event_type == "plan_generated":
        # See all planned actions at once
        for action in event.data['actions']:
            print(f"Will execute: {action['name']}")
    
    elif event.event_type == "action_completed":
        # Results stream as they complete (in parallel)
        print(f"Got result from {event.action_name}")
```

**Benefits:**
- Multiple actions execute simultaneously
- See progress in real-time
- Better resource utilization
- Faster overall execution
- More responsive UX

---

## Performance Characteristics

### Sequential (v1.0)
```
Action 1: ████████ (2s)
Action 2:         ████████ (2s)  
Action 3:                 ████████ (2s)
Total: 6 seconds
```

### Parallel (v2.0)
```
Action 1: ████████ (2s)  ┐
Action 2: ████████ (2s)  ├─ Wave 1 (parallel)
Action 3: ████████ (2s)  ┘
Total: 2 seconds (3x faster!)
```

---

## Best Practices

### 1. Use ASYNC for Independent Operations
```python
# ✅ Good - Parallel data fetching
Action("fetch_wiki", mode=ASYNC)
Action("fetch_docs", mode=ASYNC)

# ❌ Bad - Sequential when could be parallel
Action("fetch_wiki", mode=SYNC)
Action("fetch_docs", mode=SYNC)
```

### 2. Use SYNC for Critical Path
```python
# ✅ Good - Need result before continuing
Action("authenticate", mode=SYNC)
Action("fetch_user_data", depends_on=["authenticate"], mode=SYNC)
```

### 3. Use FIRE_AND_FORGET for Side Effects
```python
# ✅ Good - Don't wait for logging/caching
Action("log_action", mode=FIRE_AND_FORGET)
Action("cache_result", mode=FIRE_AND_FORGET)
```

### 4. Minimize Dependencies
```python
# ✅ Good - Only depend on what you need
Action("analyze_A", depends_on=["fetch_A"])

# ❌ Bad - Unnecessary dependency
Action("analyze_A", depends_on=["fetch_A", "fetch_B", "fetch_C"])
```

### 5. Use output_key for Data Flow
```python
# ✅ Good - Explicit data flow
Action("fetch", output_key="data")
Action("process", parameters={"input": "$data"})

# ❌ Bad - Implicit data flow (harder to debug)
```

---

## Troubleshooting

### Circular Dependencies
```python
# Error: Circular dependencies detected
Action("A", depends_on=["B"])
Action("B", depends_on=["A"])  # ❌ Circular!
```
**Fix:** Remove circular reference or restructure actions.

### Deadlocks
```python
# All actions waiting on dependencies that never complete
Action("A", depends_on=["B"])
Action("B", depends_on=["C"])
Action("C", depends_on=["missing"])  # ❌ "missing" never executes
```
**Fix:** Ensure all dependencies exist and can complete.

### Slow Execution
- Check `max_parallel` - might be too low
- Look for unnecessary SYNC modes
- Check for long-running actions blocking others
- Use ASYNC mode for independent operations

---

## Future Enhancements

- [ ] **Conditional actions** - Skip based on runtime conditions
- [ ] **Dynamic parallelism** - Auto-adjust max_parallel based on load
- [ ] **Action prioritization** - High-priority actions execute first
- [ ] **Checkpointing** - Resume execution from failure point
- [ ] **Action caching** - Cache deterministic action results
- [ ] **Distributed execution** - Execute actions across multiple workers

---

*Agent Execution Protocol v2.0 - Cortex-Prime MK1*
