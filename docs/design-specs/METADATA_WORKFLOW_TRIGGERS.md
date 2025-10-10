# LLM-Driven Metadata & Workflow Triggering System

## Overview

A system where the LLM dynamically sets metadata fields during execution, and workflows trigger automatically based on metadata state changes. The LLM self-reports its operational context (e.g., "I'm coding", "I'm debugging"), and the system responds by spawning appropriate automation workflows.

## Core Concept

**Traditional Approach:**
- Workflows triggered by explicit events (user input, time, manual)
- Agent has no self-awareness of its operational state
- Automation is external to agent's reasoning

**This Approach:**
- LLM declares its operational state via `<metadata>` tag
- Workflows listen to metadata and trigger automatically
- Agent-driven automation through self-awareness
- Non-blocking, async workflow execution

## Design Principles

1. **LLM-Driven State** - The LLM decides and declares its operational mode
2. **Auto-Injected Schema** - Metadata schema is baked into agent context, not system prompt
3. **Soft Validation** - Invalid metadata = soft error in next iteration, execution continues
4. **Persistent CRUD** - Metadata persists across iterations within session, LLM can update or leave unchanged
5. **Non-Blocking Workflows** - Workflows trigger async in background, don't block agent iteration
6. **Full Context Access** - Workflows/tools receive complete agent context (metadata, session state, capabilities)
7. **Multi-Condition Triggers** - Workflows can trigger on complex conditions (AND/OR logic across multiple fields)

## Protocol Extension

### New `<metadata>` Tag

The LLM emits a `<metadata>` tag in its response to declare/update its operational state:

```xml
<metadata>
{
  "status": "CODING",
  "priority": "HIGH",
  "mode": "AUTONOMOUS",
  "context": {
    "project": "cortex-prime",
    "phase": "implementation",
    "task": "metadata_system"
  }
}
</metadata>

<thought>
I'm now implementing the feature, so I've set status to CODING.
This will automatically trigger documentation and changelog workflows.
</thought>

<action type="tool" mode="async" id="edit">
{"name": "file_editor", "parameters": {...}}
</action>

<response final="false">
Implementing the core metadata system...
</response>
```

### Metadata Behavior

- **Optional** - LLM doesn't have to emit `<metadata>` every iteration
- **Partial Updates** - LLM only includes fields it wants to change
- **Persistent** - Values persist across iterations until changed
- **Session-Scoped** - Metadata lives only during agent execution session
- **Validated** - Invalid values cause soft errors, don't break execution

## Agent Manifest Schema

### Defining Metadata Fields

```yaml
kind: Agent
name: "coding_agent"
version: "1.0"

# Define metadata fields the LLM can set
metadata:
  fields:
    status:
      type: "enum"
      values: ["IDLE", "CODING", "PLANNING", "DEBUGGING", "TESTING", "TALKING"]
      default: "IDLE"
      description: "Current operational mode"
      
    priority:
      type: "enum"
      values: ["HIGH", "MEDIUM", "LOW"]
      default: "MEDIUM"
      description: "Task priority level"
      
    mode:
      type: "enum"
      values: ["AUTONOMOUS", "ASSISTED", "SUPERVISED"]
      default: "AUTONOMOUS"
      description: "Execution mode"
      
    context:
      type: "object"
      description: "Free-form JSON context data"
      # No schema - LLM can set any JSON structure
      
  # How metadata schema is injected into LLM context
  injection:
    method: "auto"  # Auto-inject before each iteration
    template: |
      Available metadata fields (use <metadata> tag to update):
      - status: {values} (current: {current_value})
      - priority: {values} (current: {current_value})
      - mode: {values} (current: {current_value})
      - context: any JSON object (current: {current_value})

import:
  tools: [...]
  workflows:
    - "./workflows/code_finalization.yml"
    - "./workflows/high_priority_alert.yml"
```

### Supported Field Types

| Type | Description | Example |
|------|-------------|---------|
| `enum` | Fixed set of values | `["IDLE", "CODING", "PLANNING"]` |
| `string` | Free-text string | `"any text"` |
| `number` | Numeric value | `42`, `3.14` |
| `boolean` | True/false | `true`, `false` |
| `object` | Nested JSON object | `{"key": "value", "nested": {...}}` |
| `array` | List of values | `["item1", "item2"]` |

## Workflow Triggers

### Metadata-Based Triggers

```yaml
kind: Workflow
name: "code_finalization"

trigger:
  type: "metadata_match"
  conditions:
    # Simple field match
    status: "CODING"
    
    # OR match: any of these values
    priority: ["HIGH", "MEDIUM"]
    
    # Nested object match
    context:
      phase: "implementation"
      
  # Require ALL conditions to match (AND logic)
  match_all: true
```

### Complex Trigger Examples

**Single Field:**
```yaml
trigger:
  type: "metadata_match"
  conditions:
    status: "CODING"  # Triggers when status is CODING
```

**Multiple Values (OR):**
```yaml
trigger:
  type: "metadata_match"
  conditions:
    status: ["CODING", "DEBUGGING", "TESTING"]  # Any of these
```

**Multiple Fields (AND):**
```yaml
trigger:
  type: "metadata_match"
  conditions:
    status: "DEBUGGING"
    priority: "HIGH"
    mode: "AUTONOMOUS"
  match_all: true  # All must match
```

**Nested Object Matching:**
```yaml
trigger:
  type: "metadata_match"
  conditions:
    context:
      project: "cortex"
      phase: "testing"
      severity: "critical"
  match_all: true
```

## Runtime Execution Flow

### Agent Iteration Cycle

```
Iteration N:
  1. Inject current metadata into LLM context
     ├─ Show schema/available values
     ├─ Show current metadata state
     └─ Show any soft errors from previous iteration
     
  2. LLM generates response (may include <metadata> tag)
  
  3. Parse response stream
     ├─ Extract <metadata> tag (if present)
     └─ Validate against schema
     
  4. Update session metadata
     ├─ Valid values → Update persistent state
     └─ Invalid values → Queue soft error for next iteration
     
  5. Check workflow triggers (non-blocking)
     ├─ For each workflow:
     │   ├─ Evaluate trigger conditions
     │   └─ If match → Spawn workflow async
     └─ Don't wait for workflows to complete
     
  6. Continue to next iteration
     └─ Agent loop not blocked by workflows
```

### Soft Error Handling

When LLM sets invalid metadata:

```xml
<!-- Iteration N: LLM sets invalid value -->
<metadata>
{
  "status": "COMPILING",  // Invalid - not in enum
  "priority": "CRITICAL"   // Invalid - not in enum
}
</metadata>
```

**Next Iteration (N+1) Context Injection:**
```
⚠️ Previous metadata update had errors:
  - status: "COMPILING" not in [IDLE, CODING, PLANNING, DEBUGGING, TESTING, TALKING]
  - priority: "CRITICAL" not in [HIGH, MEDIUM, LOW]
  
Current metadata (unchanged):
  - status: CODING
  - priority: HIGH
  - mode: AUTONOMOUS
  - context: {...}
```

## Workflow Context Access

### Agent Context Object

Workflows receive complete agent context:

```python
agent_context = {
    # Session info
    "session_id": "uuid-123-456",
    "agent_name": "coding_agent",
    "iteration_count": 5,
    "started_at": "2024-10-10T12:00:00Z",
    
    # Current metadata (what triggered this workflow)
    "metadata": {
        "status": "CODING",
        "priority": "HIGH",
        "mode": "AUTONOMOUS",
        "context": {
            "project": "cortex",
            "phase": "implementation"
        }
    },
    
    # Agent capabilities
    "tools": [...],
    "workflows": [...],
    "agents": [...],
    "relics": [...],
    
    # Execution history
    "actions_executed": [...],
    "thoughts": [...],
    "responses": [...],
    
    # Environment
    "environment": {...},
    "workspace_path": "/path/to/workspace",
    
    # Manifest data
    "manifest": {...}
}
```

### Using Context in Workflows

```yaml
kind: Workflow
name: "code_finalization"

trigger:
  type: "metadata_match"
  conditions:
    status: "CODING"

steps:
  - name: "update_documentation"
    type: "agent"
    target: "doc_generator"
    parameters:
      # Access metadata that triggered this workflow
      project_name: "${agent.metadata.context.project}"
      current_phase: "${agent.metadata.context.phase}"
      
      # Access session info
      session_id: "${agent.session_id}"
      iteration: "${agent.iteration_count}"
      
      # Access agent capabilities
      available_tools: "${agent.tools}"
      
  - name: "update_changelog"
    type: "tool"
    target: "changelog_updater"
    parameters:
      workspace: "${agent.workspace_path}"
      status: "${agent.metadata.status}"
      
  - name: "git_commit"
    type: "tool"
    target: "git"
    parameters:
      message: "Auto-commit from ${agent.agent_name} session ${agent.session_id}"
    condition: "previous_steps_success"
```

## Implementation Architecture

### Runtime Components

```python
class AgentSession:
    def __init__(self, agent_manifest, session_id):
        self.session_id = session_id
        self.metadata = self._init_metadata(agent_manifest)
        self.metadata_schema = agent_manifest.metadata
        self.workflows = agent_manifest.workflows
        self.iteration_count = 0
        self.soft_errors = []
        
    def _init_metadata(self, manifest):
        """Initialize metadata with default values"""
        metadata = {}
        for field, schema in manifest.metadata.fields.items():
            if 'default' in schema:
                metadata[field] = schema['default']
        return metadata
        
    async def handle_metadata_update(self, new_metadata):
        """Validate and update metadata, trigger workflows"""
        # Validate
        errors = self._validate_metadata(new_metadata)
        if errors:
            self.soft_errors.extend(errors)
            return
            
        # Update
        self.metadata.update(new_metadata)
        
        # Trigger workflows (non-blocking)
        await self._check_workflow_triggers()
        
    def _validate_metadata(self, metadata):
        """Validate metadata against schema"""
        errors = []
        for field, value in metadata.items():
            schema = self.metadata_schema.fields.get(field)
            if not schema:
                errors.append(f"Unknown field: {field}")
                continue
                
            if schema['type'] == 'enum':
                if value not in schema['values']:
                    errors.append(
                        f"{field}: '{value}' not in {schema['values']}"
                    )
        return errors
        
    async def _check_workflow_triggers(self):
        """Check all workflows for trigger matches"""
        for workflow in self.workflows:
            if self._trigger_matches(workflow.trigger):
                # Spawn async, don't await
                asyncio.create_task(
                    self._execute_workflow(workflow)
                )
                
    def _trigger_matches(self, trigger):
        """Check if trigger conditions match current metadata"""
        if trigger.type != "metadata_match":
            return False
            
        conditions = trigger.conditions
        match_all = trigger.get('match_all', True)
        
        matches = []
        for field, expected in conditions.items():
            actual = self._get_nested_value(self.metadata, field)
            
            if isinstance(expected, list):
                # OR match
                matches.append(actual in expected)
            else:
                # Exact match
                matches.append(actual == expected)
                
        return all(matches) if match_all else any(matches)
        
    async def _execute_workflow(self, workflow):
        """Execute workflow with agent context"""
        context = self._build_agent_context()
        await workflow_engine.execute(workflow, context)
        
    def _build_agent_context(self):
        """Build complete agent context for workflows/tools"""
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "iteration_count": self.iteration_count,
            "metadata": self.metadata.copy(),
            "tools": self.tools,
            "workflows": self.workflows,
            # ... etc
        }
```

### Streaming Parser Extension

```python
class StreamingProtocolParser:
    async def parse_stream(self, llm_stream):
        """Parse streaming LLM response"""
        async for chunk in llm_stream:
            # Existing parsing logic for <thought>, <action>, <response>
            
            # Add metadata parsing
            if chunk.startswith('<metadata>'):
                metadata_json = await self._extract_json_block(llm_stream)
                await self.session.handle_metadata_update(metadata_json)
                
                yield ParseEvent(
                    type="metadata_update",
                    content=metadata_json,
                    metadata={"validated": True}
                )
```

## Use Cases

### 1. Coding Agent with Auto-Documentation

```yaml
# Agent sets status when coding
metadata:
  fields:
    status:
      values: ["IDLE", "CODING", "TESTING", "DEPLOYING"]
```

**LLM Output:**
```xml
<metadata>{"status": "CODING"}</metadata>
<thought>I'm implementing the new feature...</thought>
<action>...</action>
```

**Triggered Workflows:**
- Update documentation
- Update CHANGELOG.md
- Run linters
- Prepare git commit

### 2. Emergency Response

```yaml
# Workflow triggers on high priority + error state
trigger:
  type: "metadata_match"
  conditions:
    priority: "HIGH"
    status: "ERROR"
  match_all: true
```

**LLM Output:**
```xml
<metadata>
{
  "status": "ERROR",
  "priority": "HIGH",
  "context": {"error_type": "critical_failure"}
}
</metadata>
```

**Triggered Workflows:**
- Alert escalation
- Emergency logging
- Rollback automation
- Incident report generation

### 3. Context-Aware Research Agent

```yaml
metadata:
  fields:
    mode:
      values: ["RESEARCHING", "ANALYZING", "WRITING"]
    context:
      type: "object"
```

**Different workflows per mode:**
- RESEARCHING → Bookmark URLs, save citations
- ANALYZING → Generate summaries, extract insights  
- WRITING → Grammar check, format references

## Benefits

1. **Self-Aware Agents** - LLM declares its operational state explicitly
2. **Intelligent Automation** - Workflows adapt to what agent is actually doing
3. **No Manual Workflow Management** - LLM's state drives automation automatically
4. **Non-Blocking** - Workflows run in background, don't slow agent
5. **Rich Context** - Workflows have full access to agent state and capabilities
6. **Flexible Conditions** - Complex multi-field trigger logic
7. **Soft Failures** - Invalid metadata doesn't break execution

## Future Enhancements

1. **Metadata History** - Track metadata changes over time for analysis
2. **Conditional Actions** - LLM can use metadata in action conditions
3. **Metadata Feeds** - Inject metadata into context feeds
4. **Cross-Agent Metadata** - Sub-agents inherit/share metadata
5. **Workflow Feedback** - Workflows can update agent metadata
6. **Metric Collection** - Automatic metrics based on metadata state
7. **State Visualization** - Real-time dashboard of agent metadata state

## Open Questions

1. **Metadata persistence scope** - Currently session-only. Future: persist between runs?
2. **Workflow priority** - If multiple workflows trigger, execution order?
3. **Metadata limits** - Max size for context object? Max number of fields?
4. **Workflow cancellation** - If metadata changes, cancel running workflows?
5. **Nested triggers** - Should workflows be able to trigger other workflows via metadata?

---

**Status:** Design Complete - Ready for Implementation
**Version:** 1.0
**Last Updated:** 2024-10-10
