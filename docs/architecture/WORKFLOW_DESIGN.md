# Workflow Manifest Design Specification

## Overview
This document defines the comprehensive manifest schema for Cortex-Prime MK1.

## Manifest Types

### 1. Workflow Manifests

Workflows orchestrate multi-step processes combining agents, tools, and relics.

**Key Features:**
- Sequential and parallel execution
- Conditional logic
- Error handling and retries
- Context variable resolution
- Output mapping
- Dependency tracking

**Step Types:**
- `tool` - Execute a stateless tool
- `agent` - Invoke an AI agent
- `relic` - Interact with stateful service
- `decision` - Conditional branching
- `barrier` - Wait for parallel tasks
- `workflow` - Nested workflow (recursion support)

**Example Workflows Created:**
1. `journal_entry_pipeline.workflow.yml` - Complex sequential workflow with parallel analysis
2. `simple_data_processing.workflow.yml` - Basic ETL pattern
3. `multi_agent_research.workflow.yml` - Advanced parallel agents with recursion

### 2. Tool Manifests

Tools are stateless, executable functions.

**Enhancements:**
- Detailed execution configuration
- Resource limits
- Sandboxing options
- Input/output schemas (JSON Schema)
- Error handling policies
- Health checks
- Usage examples
- Metrics tracking

**Example:** `sentiment_analyzer/tool.yml`

### 3. Agent Manifests

Already well-defined in `manifests/agents/journaler/agent.yml`

**Core Components:**
- Identity & metadata
- Behavioral profile (persona, agency_level)
- Cognitive engine (LLM config)
- Capability grants (imports)
- Sensory inputs (context_feeds)
- Environment configuration

### 4. Relic Manifests

Stateful, persistent services.

**Components:**
- Service specification
- Interface definition
- Persistence configuration
- Dependencies
- Environment

**Example:** `manifests/relics/kv_store/relic.yml`

## Context Variable System

All manifests support context variables:

**Trigger/Input Variables:**
- `$(trigger.param_name)` - Access trigger parameters
- `$(input.field)` - Access workflow inputs

**Step Output Variables:**
- `$(steps.step_name.output_field)` - Access previous step outputs
- `$(steps.step_name.status)` - Check step execution status

**System Variables:**
- `$TIMESTAMP` - Current timestamp
- `$WORKFLOW_ID` - Unique workflow execution ID
- `$SESSION_ID` - Current session ID
- `$AGENT_ID`, `$AGENT_NAME` - Agent context
- All built-in variables from context_variables.py

**Conditional Expressions:**
- String comparisons: `$(var) == 'value'`
- Numeric comparisons: `$(var) >= 0.7`
- Boolean logic: `$(var1) and $(var2)`
- List operations: `'item' in $(list_var)`
- Length checks: `len($(var)) > 0`

## Step Configuration Options

### Retry Policy
```yaml
retry_policy:
  max_attempts: 3
  backoff: "exponential"  # exponential, linear, none
  initial_delay: 1        # seconds
  max_delay: 60           # seconds
```

### Failure Handling
```yaml
on_failure: "continue"  # continue, abort, retry, log_only
```

### Parallel Execution
```yaml
parallel_group: "group_name"  # All steps in same group run in parallel
```

### Conditions
```yaml
condition: "$(previous_step.status) == 'success'"
```

### Output Mapping
```yaml
output_mapping:
  custom_name: "$.json.path"
  another_field: "$.nested.value"
```

## Workflow Execution Flow

1. **Trigger** - Workflow starts via manual, scheduled, event, or webhook
2. **Step Execution** - Steps execute based on conditions and dependencies
3. **Parallel Groups** - Steps in same `parallel_group` run concurrently
4. **Barriers** - Wait for parallel groups to complete
5. **Decisions** - Branch based on expressions
6. **Error Handling** - Retry, continue, or abort based on policy
7. **Outputs** - Map step outputs to workflow outputs

## Dependency Resolution

Workflows declare dependencies:
```yaml
dependencies:
  agents: ["agent_name"]
  tools: ["tool_name"]
  relics: ["relic_name"]
  workflows: ["nested_workflow_name"]
```

The manifest ingestion service validates all dependencies exist before allowing workflow execution.

## Testing Strategy

1. **Simple Workflow** - Test basic sequential execution
2. **Parallel Workflow** - Test concurrent step execution
3. **Conditional Workflow** - Test decision branches
4. **Nested Workflow** - Test workflow recursion
5. **Error Handling** - Test retry policies and failure modes

## Implementation Notes

### Pydantic Models
The WorkflowStep and WorkflowManifest models in `manifest_models.py` need enhancement:

**Required Updates:**
- Add `parallel_group` field to WorkflowStep
- Add `on_failure` field to WorkflowStep
- Add `output_mapping` field to WorkflowStep
- Add `configuration` field to WorkflowManifest
- Add `outputs` field to WorkflowManifest
- Enhance `retry_policy` structure
- Add step type validation

### Workflow Executor
A new service component needed:
- Parse workflow manifest
- Execute steps in order
- Handle parallel groups
- Evaluate conditions
- Manage retries
- Track outputs
- Handle errors

## Next Steps

1. ✅ Create example workflow manifests
2. ⏭️ Update Pydantic models to match enhanced schema
3. ⏭️ Implement workflow executor service
4. ⏭️ Add workflow validation tests
5. ⏭️ Test workflow execution engine
6. ⏭️ Document workflow best practices

---

**The cathedral needs workflows to come alive.** 🏛️
