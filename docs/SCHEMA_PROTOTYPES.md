# Chimera Agent JSON Schema Prototypes

This document is a design space for evolving the core JSON communication schema used by agents in the Chimera Ecosystem. Its purpose is to carefully design and prototype new features to avoid the limitations of previous projects, particularly around asynchronous operations and context management.

---

## Schema v1.0: Synchronous Baseline

This is the current operational schema. It's robust for synchronous, single-turn actions.

```json
{
  "status": "string (Enum: SUCCESS | EXECUTING | ERROR | ...)",
  "thoughts": [
    {
      "type": "string (Enum: PLAN | OBSERVATION | ...)",
      "content": "string"
    }
  ],
  "actions": [
    {
      "action": "string",
      "type": "string (Enum: tool | script | internal)",
      "params": "object",
      "execution": "string (Enum: SYNC | ASYNC | ...)",
      "confidence": "float",
      "warnings": ["string"]
    }
  ],
  "stop": "boolean",
  "response": "string | null"
}
```

---

## Schema v2.0 (Prototype): Asynchronous Operations & Context Management

This prototype introduces concepts for handling long-running (asynchronous) tool calls and explicit context passing.

### Key Additions:

1.  **`task_id` in Action:** When an `ASYNC` action is dispatched, the system immediately returns a `task_id`.
2.  **New `status`:** A `TASK_STARTED` status to indicate that an async process has been initiated.
3.  **`context` Block:** A new top-level block to define the context for the current operation.

### Example v2.0 Prototype: Kicking off an Async Task

**Scenario:** The user asks the agent to start a long-running code compilation.

```json
{
  "status": "TASK_STARTED",
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The Master has requested a compilation. This is a long-running task. I will dispatch it as an asynchronous action using the 'build_tool' and immediately return a task ID so the Master is not blocked."
    },
    {
      "type": "DECISION",
      "content": "Using 'build_tool' with 'target: //main:app' as an ASYNC action."
    }
  ],
  "actions": [
    {
      "action": "build_tool",
      "type": "tool",
      "params": {
        "target": "//main:app",
        "config": "release"
      },
      "execution": "ASYNC"
    }
  ],
  "stop": true,
  "response": "Compilation task started. You can check the status using the task ID: a7b3c9d1-e4f6-4g8h-9i1j-k2l3m4n5o6p7"
}
```

### Example v2.0 Prototype: Context Management

**Scenario:** The user wants to summarize a document, but the agent needs to know which knowledge "relic" to use.

```json
{
  "status": "EXECUTING",
  "context": {
    "knowledge_relics": ["relic_id_project_docs_v2"],
    "security_level": "user"
  },
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The user wants a summary. I will use the 'summarizer' tool, but I will explicitly scope its context to the 'project_docs_v2' knowledge relic to ensure it doesn't pull from irrelevant sources."
    }
  ],
  "actions": [
    {
      "action": "summarizer_tool",
      "type": "tool",
      "params": {
        "query": "Provide a summary of the new architecture.",
        "target_document": "architecture.md"
      }
    }
  ],
  "stop": false,
  "response": null
}
```
