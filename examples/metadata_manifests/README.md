# Metadata Manifest System - Examples

## Overview

The **Metadata manifest** is a new manifest type that defines:
1. **Fields** - What metadata the LLM can set via `<metadata>` tag
2. **Hooks** - Automation that triggers when metadata matches conditions

Agents import metadata manifests, gaining both the fields and the automation hooks.

## Structure

```
examples/metadata_manifests/
├── metadata/              # Metadata manifest definitions
│   ├── dev_metadata.yml         # Development workflows
│   ├── research_metadata.yml    # Research workflows
│   └── devops_metadata.yml      # DevOps workflows
├── agents/                # Agents that import metadata
│   ├── coding_agent.yml
│   ├── research_agent.yml
│   └── devops_agent.yml
└── workflows/             # Workflows triggered by hooks
    └── (referenced by metadata manifests)
```

## Metadata Manifest Format

```yaml
kind: Metadata
name: "dev_metadata"

# What the LLM can set
fields:
  status:
    type: "enum"
    values: ["IDLE", "CODING", "TESTING"]
    default: "IDLE"

# What triggers when metadata changes
metadata_hooks:
  - id: "coding_automation"
    when:
      metadata:
        status: "CODING"
    actions:
      - type: "workflow"
        target: "code_finalization"
        params:
          project: "${metadata.context.project}"
```

## Agent Import

```yaml
kind: Agent
name: "coding_agent"

import:
  # Import metadata manifest
  metadata:
    - "./metadata/dev_metadata.yml"
  
  # Import resources used by hooks
  workflows:
    - "./workflows/code_finalization.yml"
  tools:
    - "linter"
```

## LLM Usage

```xml
<!-- LLM sets metadata -->
<metadata>
{
  "status": "CODING",
  "priority": "HIGH",
  "context": {"project": "cortex"}
}
</metadata>

<thought>
Setting status to CODING triggers dev_metadata hooks:
- code_finalization workflow
- linter tool
These run automatically in the background.
</thought>
```

## Examples Included

### 1. Development Metadata (`dev_metadata.yml`)
**Fields:**
- `status`: IDLE | CODING | TESTING | DEBUGGING | REVIEWING | DEPLOYING
- `priority`: LOW | MEDIUM | HIGH | CRITICAL
- `mode`: AUTONOMOUS | ASSISTED | SUPERVISED
- `context`: object

**Hooks:**
- `status: CODING` → Run linter, code_finalization workflow
- `status: TESTING` + `priority: HIGH|CRITICAL` → Comprehensive tests
- `status: DEBUGGING` + `priority: CRITICAL` → Create bug ticket, enable debug logging
- `status: DEPLOYING` + `context.environment: production` → Pre-deploy checks, audit logging

### 2. Research Metadata (`research_metadata.yml`)
**Fields:**
- `mode`: RESEARCHING | ANALYZING | WRITING | REVIEWING
- `topic`: string
- `depth`: SHALLOW | MODERATE | DEEP
- `context`: object

**Hooks:**
- `mode: RESEARCHING` + `depth: DEEP` → Bookmark sources, extract citations, store in knowledge base
- `mode: ANALYZING` → Trigger data_analyzer agent, summarizer tool
- `mode: WRITING` → Grammar check, citation formatting, plagiarism check
- `mode: REVIEWING` → Fact checking, quality review

### 3. DevOps Metadata (`devops_metadata.yml`)
**Fields:**
- `phase`: PLANNING | DEPLOYING | MONITORING | INCIDENT | ROLLBACK
- `environment`: DEV | STAGING | PRODUCTION
- `severity`: LOW | MEDIUM | HIGH | CRITICAL
- `context`: object

**Hooks:**
- `phase: DEPLOYING` + `environment: PRODUCTION` → Pre-deploy validation, approval gate, enhanced monitoring
- `phase: DEPLOYING` + `environment: STAGING|DEV` → Automated deployment
- `phase: INCIDENT` + `severity: HIGH|CRITICAL` + `environment: PRODUCTION` → Page on-call, capture state, prepare rollback
- `phase: ROLLBACK` → Execute rollback pipeline

## Hook Action Types

Hooks can invoke any manifest type:

```yaml
actions:
  - type: "workflow"
    target: "workflow_name"
    params: {...}
    
  - type: "tool"
    target: "tool_name"
    params: {...}
    
  - type: "agent"
    target: "agent_name"
    params: {...}
    
  - type: "relic"
    target: "relic_name"
    params: {...}
```

## Variable Substitution

Available variables in hook params:

- `${metadata.field}` - Any metadata field
- `${metadata.context.nested}` - Nested context values
- `${session_id}` - Current session ID
- `${workspace_path}` - Agent workspace path
- `${agent_name}` - Agent name

Example:
```yaml
params:
  project: "${metadata.context.project}"
  session: "${session_id}"
  severity: "${metadata.severity}"
```

## Key Benefits

1. **Reusable Metadata** - Multiple agents can import the same metadata manifest
2. **Centralized Automation** - Hooks defined once, used by all importing agents
3. **Type Safety** - Metadata fields validated against schema
4. **Flexibility** - Hooks can invoke any manifest type (workflow, tool, agent, relic)
5. **Context-Aware** - Full access to metadata and session context in hooks

## Design Patterns

### Pattern 1: Status-Based Automation
```yaml
# LLM changes status → Hooks trigger appropriate workflows
fields:
  status: [...]

metadata_hooks:
  - when: {status: "CODING"}
    actions: [linter, docs]
```

### Pattern 2: Multi-Condition Triggers
```yaml
# Complex conditions with AND logic
metadata_hooks:
  - when:
      status: "INCIDENT"
      severity: "CRITICAL"
      environment: "PRODUCTION"
    actions: [alert, rollback]
```

### Pattern 3: OR Conditions
```yaml
# Trigger on any of multiple values
metadata_hooks:
  - when:
      priority: ["HIGH", "CRITICAL"]
    actions: [...]
```

### Pattern 4: Context-Aware Actions
```yaml
# Use metadata values in action parameters
actions:
  - type: "workflow"
    params:
      env: "${metadata.environment}"
      issue: "${metadata.context.issue_id}"
```

---

**Status:** Design Examples - Non-functional manifests for specification purposes
