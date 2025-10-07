# Cortex-Prime MK1 - Manifest Reference

> **"Declarative reality for sovereign AI entities."**

Complete reference for all manifest types in the Cortex-Prime ecosystem.

---

## Table of Contents

1. [Overview](#overview)
2. [Manifest Philosophy](#manifest-philosophy)
3. [Common Fields](#common-fields)
4. [Agent Manifests](#agent-manifests)
5. [Tool Manifests](#tool-manifests)
6. [Relic Manifests](#relic-manifests)
7. [Workflow Manifests](#workflow-manifests)
8. [Monument Manifests](#monument-manifests)
9. [Amulet Manifests](#amulet-manifests)
10. [Context Variables](#context-variables)
11. [Import System](#import-system)
12. [Best Practices](#best-practices)
13. [Examples](#examples)

---

## Overview

Manifests are **declarative YAML specifications** that define sovereign entities in the Cortex-Prime ecosystem. Each manifest is a complete, self-contained definition that can be:

- **Parsed** and validated by the manifest ingestion service
- **Hot-reloaded** when files change
- **Composed** with other manifests via imports
- **Versioned** and tracked
- **Deployed** across distributed systems

### Supported Formats

- **Pure YAML:** `.yml`, `.yaml`
- **Markdown with YAML frontmatter:** `.md`, `.markdown`

---

## Manifest Philosophy

### Fractal Composability

**ANY manifest can import ANY other manifest.**

```
Agent → Agent    (hierarchical sub-agents)
Agent → Tool     (capabilities)
Agent → Relic    (state management)
Agent → Workflow (orchestration)
Tool → Agent     (intelligent processing)
Tool → Tool      (chaining)
Relic → Workflow (automation)
Workflow → *     (full composition)
```

### Sovereign Identity

Every manifest has:
- Unique `name` within its type
- Clear `version` for compatibility tracking
- Explicit `state` (stable, unstable, deprecated)
- Attribution via `author`

### Declarative Reality

Manifests define **WHAT** entities are, not **HOW** they execute. The arbiter core interprets and orchestrates.

---

## Common Fields

All manifests share these required fields:

```yaml
kind: Agent | Tool | Relic | Workflow | Monument | Amulet
version: "1.0"              # Semantic versioning
name: "entity_name"         # Unique identifier (snake_case)
summary: "Brief description"
author: "CREATOR_NAME"
state: stable | unstable | deprecated
```

### Optional Common Fields

```yaml
description: |
  Multi-line detailed description
  Supports markdown formatting

tags:
  - "category"
  - "feature"
  - "use-case"

metadata:
  custom_field: "value"
  another_field: 123
```

---

## Agent Manifests

Agents are **autonomous AI entities** with cognitive capabilities, personality, and agency.

### Full Schema

```yaml
kind: Agent
version: "1.0"
name: "agent_name"
summary: "Brief agent description"
author: "PRAETORIAN_CHIMERA"
state: "stable"

# --- BEHAVIORAL PROFILE ---
persona:
  agent: "./system-prompts/agent.md"      # Required: Agent identity/personality
  user: "./system-prompts/user.md"        # Optional: User interaction style
  system: "./system-prompts/system.md"    # Optional: System-level directives

agency_level: strict | default | loose | autonomous
grade: common | uncommon | rare | epic | legendary
iteration_cap: 10  # Max OODA loops per task

# --- COGNITIVE ENGINE ---
cognitive_engine:
  primary:
    provider: "google" | "ollama" | "openai" | "anthropic"
    model: "gemini-1.5-flash"
  
  fallback:
    provider: "ollama"
    model: "llama3.1:8b"
  
  parameters:
    temperature: 0.7      # 0.0 = deterministic, 2.0 = creative
    top_p: 0.9
    top_k: 40
    max_tokens: 4096
    stream: true
    stop_sequences: []

# --- CAPABILITY GRANTS (Imports) ---
import:
  agents:
    - "./agents/sub_agent/agent.yml"
    - "global_agent_name"
  
  tools:
    - "./tools/custom_tool/tool.yml"
    - "file_system"  # Global tool
  
  relics:
    - "./relics/memory_store/relic.yml"
  
  workflows:
    - "./workflows/task_pipeline.workflow.yml"
  
  monuments:
    - "InternetArchive-Monument"
  
  amulets:
    - "verbose_mode"
    - "fact_checker"

# --- SENSORY INPUTS (Context Feeds) ---
context_feeds:
  - id: "current_time"
    type: "on_demand" | "periodic" | "event"
    interval: 60  # seconds (for periodic)
    source:
      type: "internal" | "relic" | "tool" | "external"
      name: "source_name"
      action: "method_to_call"
      params:
        key: "value"
  
  - id: "user_context"
    type: "on_demand"
    source:
      type: "internal"
      action: "get_user_context"

# --- ENVIRONMENT ---
environment:
  env_file: [".env", ".env.local"]
  variables:
    WORKSPACE: "$HOME/agents/$AGENT_NAME"
    LOG_LEVEL: "INFO"
    MAX_RETRIES: "3"
  
  resources:
    requests:
      cpu: "0.5"
      memory: "512Mi"
    limits:
      cpu: "2.0"
      memory: "2Gi"
    storage: "10Gi"

# --- METRICS & OBSERVABILITY ---
metrics:
  track_llm_calls: true
  track_tool_usage: true
  track_token_usage: true
  custom_metrics:
    - name: "task_success_rate"
      type: "gauge"

tags:
  - "category"
  - "capability"
```

### Agency Levels

| Level | Description | Autonomy |
|-------|-------------|----------|
| `strict` | Agent must ask permission for every action | Lowest |
| `default` | Agent can use granted tools, asks for high-risk actions | Balanced |
| `loose` | Agent has broad autonomy, minimal oversight | High |
| `autonomous` | Full autonomy, no human approval needed | Highest |

### Grade Levels

| Grade | Priority | Resource Allocation | Use Case |
|-------|----------|---------------------|----------|
| `common` | Normal | Standard | General tasks |
| `uncommon` | Elevated | +25% | Important tasks |
| `rare` | High | +50% | Critical tasks |
| `epic` | Very High | +100% | Mission-critical |
| `legendary` | Maximum | Unlimited | System-critical |

### Example: Simple Agent

```yaml
kind: Agent
version: "1.0"
name: "code_reviewer"
summary: "Reviews code for quality and security issues"
author: "PRAETORIAN_CHIMERA"
state: "stable"

persona:
  agent: "./system-prompts/code_reviewer.md"

agency_level: "default"
grade: "common"
iteration_cap: 5

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"
  parameters:
    temperature: 0.3
    max_tokens: 4096

import:
  tools:
    - "file_system"
    - "code_analyzer"

environment:
  variables:
    CODE_STANDARDS: "pep8,eslint"
```

---

## Tool Manifests

Tools are **stateless, executable functions** that agents can invoke.

### Full Schema

```yaml
kind: Tool
version: "1.0"
name: "tool_name"
summary: "Brief tool description"
author: "PRAETORIAN_CHIMERA"
state: "stable"

description: |
  Detailed description of what the tool does,
  its capabilities, and use cases.

# --- EXECUTION CONFIGURATION ---
execution:
  type: "script" | "container" | "http" | "grpc"
  runtime: "python3" | "bash" | "node" | "deno"
  entrypoint: "./scripts/tool.py"
  
  resources:
    memory: "512M"
    cpu: "0.5"
    timeout: 30  # seconds
  
  sandbox:
    enabled: true
    network: "none" | "localhost" | "internet"
    filesystem:
      read_only: true
      allowed_paths:
        - "/app/data"
        - "/tmp"
      blocked_paths:
        - "/etc/passwd"

# --- BUILD CONFIGURATION ---
build:
  engine: "pip" | "npm" | "cargo" | "docker"
  requirements_file: "./requirements.txt"
  dockerfile: "./Dockerfile"
  cache_dependencies: true
  
  pre_build:
    - "command to run before build"
  
  post_build:
    - "command to run after build"

# --- PARAMETERS SCHEMA (JSON Schema) ---
parameters_schema:
  type: "object"
  required: ["param1"]
  properties:
    param1:
      type: "string"
      description: "Description of parameter"
      min_length: 1
      max_length: 1000
    
    param2:
      type: "integer"
      description: "Numeric parameter"
      minimum: 0
      maximum: 100
      default: 10
    
    param3:
      type: "boolean"
      default: false
    
    param4:
      type: "array"
      items:
        type: "string"
      min_items: 1
    
    param5:
      type: "object"
      properties:
        nested_field: 
          type: "string"

# --- OUTPUT SCHEMA (JSON Schema) ---
output_schema:
  type: "object"
  properties:
    result:
      type: "string"
      description: "Tool execution result"
    
    status:
      type: "string"
      enum: ["success", "error", "partial"]
    
    metadata:
      type: "object"
      optional: true

# --- ERROR HANDLING ---
error_handling:
  retry_on:
    - "TimeoutError"
    - "NetworkError"
  max_retries: 3
  timeout_action: "return_error" | "kill_process"
  
  error_schema:
    type: "object"
    properties:
      error_type: 
        type: "string"
      error_message:
        type: "string"

# --- HEALTH CHECK ---
health_check:
  type: "script" | "http" | "tcp"
  command: "python ./scripts/tool.py --health"
  endpoint: "/health"  # for http type
  expected_exit_code: 0
  expected_output_contains: "healthy"
  interval: 60  # seconds
  timeout: 10

# --- EXAMPLES ---
examples:
  - description: "Basic usage"
    input:
      param1: "test_value"
      param2: 42
    expected_output:
      result: "success"
      status: "success"

# --- IMPORTS (Tools can import too!) ---
import:
  agents:
    - "./agents/helper_agent/agent.yml"  # For intelligent processing
  tools:
    - "dependency_tool"
  relics:
    - "./relics/cache/relic.yml"

# --- METRICS ---
metrics:
  track_latency: true
  track_error_rate: true
  track_usage_count: true
  custom_metrics:
    - name: "custom_metric"
      type: "counter" | "gauge" | "histogram"

tags:
  - "category"
  - "capability"

# --- DEPENDENCIES ---
dependencies:
  python_packages:
    - "package>=1.0.0"
  system_packages:
    - "ffmpeg"
  models:
    - name: "model-name"
      source: "huggingface"
      size: "500MB"

environment:
  variables:
    TOOL_CONFIG: "value"
```

### Example: Simple Tool

```yaml
kind: Tool
version: "1.0"
name: "json_validator"
summary: "Validates JSON against a schema"
author: "PRAETORIAN_CHIMERA"
state: "stable"

execution:
  type: "script"
  runtime: "python3"
  entrypoint: "./scripts/validator.py"
  resources:
    memory: "256M"
    timeout: 10

parameters_schema:
  type: "object"
  required: ["json_data", "schema"]
  properties:
    json_data:
      type: "string"
    schema:
      type: "object"

output_schema:
  type: "object"
  properties:
    valid:
      type: "boolean"
    errors:
      type: "array"

tags:
  - "validation"
  - "json"
```

---

## Relic Manifests

Relics are **stateful, persistent services** that provide storage, caching, or external system integration.

### Full Schema

```yaml
kind: Relic
version: "1.0"
name: "relic_name"
summary: "Brief relic description"
author: "PRAETORIAN_CHIMERA"
state: "stable"

description: |
  Detailed description of the relic,
  what it stores, and how it's used.

service_type: "database" | "cache" | "vector_store" | "api_gateway" | "message_queue"

# --- INTERFACE DEFINITION ---
interface:
  type: "rest_api" | "grpc" | "graphql" | "socket"
  base_url: "http://relic-service:8080"
  
  endpoints:
    - name: "store"
      method: "POST" | "GET" | "PUT" | "DELETE"
      path: "/store"
      parameters:
        key:
          type: "string"
          required: true
        value:
          type: "object"
          required: true
      description: "Store a key-value pair"
    
    - name: "retrieve"
      method: "GET"
      path: "/retrieve/{key}"
      parameters:
        key:
          type: "string"
          required: true
      description: "Retrieve value by key"
  
  authentication:
    type: "bearer" | "api_key" | "basic" | "none"
    token_env: "RELIC_API_KEY"

# --- PERSISTENCE CONFIGURATION ---
persistence:
  type: "persistent_volume" | "ephemeral" | "external"
  size: "10Gi"
  storage_class: "fast-ssd"
  
  backup:
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention: 7  # days
    destination: "s3://backups/relic"

# --- DEPLOYMENT ---
deployment:
  type: "docker" | "kubernetes" | "external"
  replicas: 1
  docker_compose_file: "./docker-compose.yml"
  
  health_check:
    endpoint: "/health"
    interval: 30
    timeout: 10

# --- IMPORTS (Relics can import workflows!) ---
import:
  workflows:
    - "./workflows/cleanup.workflow.yml"
    - "./workflows/optimization.workflow.yml"
  tools:
    - "data_transformer"
  relics:
    - "../companion_relic/relic.yml"

# --- AUTOMATION ---
automation:
  scheduled_workflows:
    - workflow: "cleanup"
      schedule: "0 0 * * 0"  # Weekly
      parameters:
        max_age_days: 30
    
    - workflow: "optimization"
      schedule: "0 3 * * 1"  # Monday 3 AM

tags:
  - "storage"
  - "persistent"

dependencies:
  - "redis"
  - "postgresql"

environment:
  variables:
    DB_HOST: "localhost"
    DB_PORT: "5432"
    CACHE_SIZE: "1000"
```

### Example: Simple KV Store Relic

```yaml
kind: Relic
version: "1.0"
name: "session_cache"
summary: "Redis-based session cache"
author: "PRAETORIAN_CHIMERA"
state: "stable"

service_type: "cache"

interface:
  type: "rest_api"
  endpoints:
    - name: "set"
      method: "POST"
      path: "/set"
    - name: "get"
      method: "GET"
      path: "/get/{key}"

persistence:
  type: "persistent_volume"
  size: "5Gi"

deployment:
  type: "docker"
  docker_compose_file: "./docker-compose.yml"

tags:
  - "cache"
  - "redis"
```

---

## Workflow Manifests

Workflows are **multi-step pipelines** that orchestrate agents, tools, and relics.

### Full Schema

```yaml
kind: Workflow
version: "1.0"
name: "workflow_name"
summary: "Brief workflow description"
author: "PRAETORIAN_CHIMERA"
state: "stable"

description: |
  Detailed workflow description,
  purpose, and expected outcomes.

# --- TRIGGER CONFIGURATION ---
trigger:
  type: "manual" | "scheduled" | "event" | "webhook"
  event: "event.name"  # For event-based
  schedule: "0 0 * * *"  # Cron syntax for scheduled
  webhook_path: "/webhook/path"  # For webhook
  
  parameters:
    param1: "string"
    param2: "integer"
    param3: "array<string>"

# --- WORKFLOW STEPS ---
steps:
  # Sequential step
  - name: "step_name"
    type: "tool" | "agent" | "relic" | "decision" | "barrier" | "workflow"
    target: "entity_name"
    parameters:
      param1: "$(trigger.param1)"
      param2: "value"
    condition: "$(steps.previous.status) == 'success'"
    retry_policy:
      max_attempts: 3
      backoff: "exponential" | "linear" | "none"
      initial_delay: 1
      max_delay: 60
    on_failure: "continue" | "abort" | "retry" | "log_only"
    output_mapping:
      custom_name: "$.json.path"
  
  # Parallel steps (same parallel_group runs concurrently)
  - name: "parallel_step_1"
    type: "agent"
    target: "agent_name"
    parallel_group: "group_a"
    parameters: {}
  
  - name: "parallel_step_2"
    type: "tool"
    target: "tool_name"
    parallel_group: "group_a"
    parameters: {}
  
  # Wait for parallel group
  - name: "wait_for_parallel"
    type: "barrier"
    target: "group_a"
    timeout: 60
  
  # Decision step
  - name: "check_condition"
    type: "decision"
    target: "expression_evaluator"
    parameters:
      expression: "$(steps.previous.value) > 0.7"
  
  # Conditional step
  - name: "conditional_action"
    type: "tool"
    target: "tool_name"
    condition: "$(steps.check_condition.result) == true"
    parameters: {}
  
  # Nested workflow
  - name: "nested_workflow"
    type: "workflow"
    target: "another_workflow"
    parameters:
      input: "$(steps.previous.output)"

# --- CONFIGURATION ---
configuration:
  timeout: 600  # seconds
  
  default_retry_policy:
    max_attempts: 3
    backoff: "exponential"
    initial_delay: 1
    max_delay: 60
  
  parallel:
    enabled: true
    max_concurrent_steps: 5
  
  error_handling:
    on_step_failure: "continue" | "abort"
    collect_errors: true
    error_output: "errors"
  
  observability:
    log_level: "INFO" | "DEBUG" | "WARNING"
    trace_enabled: true
    metrics_enabled: true

# --- OUTPUTS ---
outputs:
  output1:
    source: "steps.step_name.field"
    description: "Output description"
    optional: false
  
  output2:
    source: "steps.another_step.value"
    description: "Another output"
    optional: true

# --- IMPORTS ---
import:
  agents:
    - "agent_name"
  tools:
    - "tool_name"
  relics:
    - "relic_name"
  workflows:
    - "nested_workflow"  # Can be recursive!

environment:
  variables:
    WORKFLOW_TIMEOUT: "600"
    MAX_RETRIES: "3"

tags:
  - "automation"
  - "pipeline"
```

### Step Types

| Type | Purpose | Example |
|------|---------|---------|
| `tool` | Execute stateless tool | Run sentiment analysis |
| `agent` | Invoke AI agent | Delegate research task |
| `relic` | Interact with stateful service | Store in database |
| `decision` | Conditional branching | Check if confidence > 0.7 |
| `barrier` | Wait for parallel tasks | Sync parallel group |
| `workflow` | Nested workflow | Call sub-workflow |

### Example: Simple ETL Workflow

```yaml
kind: Workflow
version: "1.0"
name: "data_etl"
summary: "Extract, transform, load data pipeline"
author: "PRAETORIAN_CHIMERA"
state: "stable"

trigger:
  type: "manual"
  parameters:
    data_url: "string"

steps:
  - name: "extract"
    type: "tool"
    target: "http_client"
    parameters:
      url: "$(trigger.data_url)"
  
  - name: "transform"
    type: "tool"
    target: "data_transformer"
    parameters:
      data: "$(steps.extract.response)"
    condition: "$(steps.extract.status) == 'success'"
  
  - name: "load"
    type: "relic"
    target: "data_warehouse"
    parameters:
      data: "$(steps.transform.output)"
    condition: "$(steps.transform.status) == 'success'"

configuration:
  timeout: 300

outputs:
  record_count:
    source: "steps.load.count"

import:
  tools:
    - "http_client"
    - "data_transformer"
  relics:
    - "data_warehouse"
```

---

## Monument Manifests

Monuments are **external systems** that agents can interact with (APIs, databases, services).

### Schema

```yaml
kind: Monument
version: "1.0"
name: "monument_name"
summary: "External system description"
author: "PRAETORIAN_CHIMERA"
state: "stable"

description: |
  Description of the external system,
  what it provides, and how to access it.

system_type: "api" | "database" | "service" | "platform"

# --- CONNECTION CONFIGURATION ---
connection:
  type: "http" | "grpc" | "socket" | "jdbc"
  base_url: "https://api.external-service.com"
  
  authentication:
    type: "oauth2" | "api_key" | "bearer" | "basic"
    credentials_env: "MONUMENT_API_KEY"
  
  rate_limiting:
    requests_per_second: 10
    requests_per_hour: 1000

# --- AVAILABLE OPERATIONS ---
operations:
  - name: "search"
    method: "GET"
    path: "/search"
    parameters:
      query:
        type: "string"
        required: true
    response_schema:
      type: "object"

tags:
  - "external"
  - "api"
```

---

## Amulet Manifests

Amulets are **behavior modifiers** that change how agents behave without changing their core definition.

### Schema

```yaml
kind: Amulet
version: "1.0"
name: "amulet_name"
summary: "Behavior modification description"
author: "PRAETORIAN_CHIMERA"
state: "stable"

description: |
  What this amulet modifies and how it affects agent behavior.

modifier_type: "directive" | "constraint" | "enhancement" | "filter"

# --- MODIFICATION SPECIFICATION ---
modifications:
  - target: "persona" | "parameters" | "tools" | "permissions"
    action: "add" | "remove" | "modify" | "replace"
    content: |
      Modification content or directive text

# --- ACTIVATION CONDITIONS ---
activation:
  type: "manual" | "automatic" | "conditional"
  condition: "expression"  # For conditional

tags:
  - "behavior"
  - "modifier"
```

### Example: Verbose Mode Amulet

```yaml
kind: Amulet
version: "1.0"
name: "verbose_mode"
summary: "Makes agents explain their reasoning in detail"
author: "PRAETORIAN_CHIMERA"
state: "stable"

modifier_type: "directive"

modifications:
  - target: "persona"
    action: "add"
    content: |
      You must explain your reasoning process in detail.
      For every decision, provide:
      1. What information you considered
      2. Why you chose this approach
      3. What alternatives you rejected and why

activation:
  type: "manual"

tags:
  - "verbose"
  - "explanation"
```

---

## Context Variables

All manifests support context variable resolution using `$(VARIABLE)` or `${VARIABLE}` syntax.

### Built-in Variables

**Core System:**
```yaml
$TIMESTAMP         # Current UTC timestamp (ISO 8601)
$TIMESTAMP_UNIX    # Unix epoch timestamp
$DATE              # YYYY-MM-DD
$TIME              # HH:MM:SS
$DATETIME          # YYYY-MM-DD HH:MM:SS
```

**Agent Identity:**
```yaml
$AGENT_ID          # Unique agent identifier
$AGENT_NAME        # Agent name
$AGENT_VERSION     # Agent version
```

**Session Context:**
```yaml
$SESSION_ID        # Current session ID
$USER_ID           # User identifier
$USER_INTENT       # User's stated goal
```

**Execution State:**
```yaml
$ITERATION_COUNT   # Current OODA loop iteration
$LAST_RESULT       # Result of last operation
$CONFIDENCE        # Confidence score (0.0-1.0)
$ERROR_COUNT       # Errors in current session
```

**Environment:**
```yaml
$HOME              # Home directory
$USER              # System user
$PWD               # Present working directory
$HOSTNAME          # System hostname
```

**Task Context:**
```yaml
$TASK_ID           # Current task ID
$TASK_STATUS       # Task status
$TASK_PRIORITY     # Task priority
```

**Workflow Context (in workflows):**
```yaml
$WORKFLOW_ID       # Unique workflow execution ID
$(trigger.param)   # Access trigger parameters
$(steps.step_name.output)  # Access step outputs
$(steps.step_name.status)  # Check step status
```

### Usage Examples

```yaml
environment:
  variables:
    WORKSPACE: "$HOME/workspace/$AGENT_NAME"
    # Resolves to: /home/cortex/workspace/my_agent
    
    LOG_FILE: "/logs/$SESSION_ID-$TIMESTAMP.log"
    # Resolves to: /logs/sess123-2025-01-01T12:00:00Z.log

context_feeds:
  - id: "iteration_info"
    source:
      params:
        message: "Iteration $ITERATION_COUNT with confidence $CONFIDENCE"
```

### Conditional Expressions

In workflows, conditions support:

```yaml
# String comparison
condition: "$(steps.previous.status) == 'success'"

# Numeric comparison
condition: "$(steps.analyze.confidence) >= 0.7"

# Boolean logic
condition: "$(var1) and $(var2)"
condition: "$(var1) or $(var2)"

# List operations
condition: "'item' in $(list_var)"
condition: "len($(list_var)) > 0"

# Nested access
condition: "$(steps.parse.data.field) == 'value'"
```

---

## Import System

### Path Resolution

**Relative paths** (from manifest file location):
```yaml
import:
  agents:
    - "./agents/sub_agent/agent.yml"           # Sibling directory
    - "../shared/agents/common/agent.yml"      # Parent directory
    - "../../global/agents/helper/agent.yml"   # Up two levels
```

**Absolute paths** (from manifest root):
```yaml
import:
  tools:
    - "tools/global_tool/tool.yml"
    - "manifests/tools/shared/tool.yml"
```

**Global references** (no path):
```yaml
import:
  tools:
    - "file_system"      # Global tool
    - "web_scraper"      # No .yml = global registry lookup
```

### Import Examples

**Agent importing everything:**
```yaml
import:
  agents:
    - "./agents/specialist/agent.yml"
  tools:
    - "./tools/analyzer/tool.yml"
    - "global_tool"
  relics:
    - "./relics/memory/relic.yml"
  workflows:
    - "./workflows/pipeline.workflow.yml"
```

**Tool importing agent (for intelligent processing):**
```yaml
import:
  agents:
    - "./agents/document_parser/agent.yml"
  tools:
    - "ocr_engine"
```

**Relic importing workflows (for automation):**
```yaml
import:
  workflows:
    - "./workflows/cleanup.workflow.yml"
    - "./workflows/optimization.workflow.yml"
```

**Workflow importing everything:**
```yaml
import:
  agents:
    - "researcher_agent"
  tools:
    - "data_validator"
  relics:
    - "result_cache"
  workflows:
    - "nested_workflow"  # Can be recursive!
```

### Dependency Resolution

The manifest ingestion service:

1. **Parses** the manifest
2. **Resolves** all import paths (relative → absolute)
3. **Recursively loads** imported manifests
4. **Detects** circular dependencies
5. **Validates** all imports exist
6. **Builds** dependency graph
7. **Registers** in topological order

---

## Best Practices

### Naming Conventions

- **Manifests:** `snake_case` for names
- **Files:** `manifest_name.yml` or `manifest_name.workflow.yml`
- **Directories:** Match manifest names
- **Variables:** `UPPER_SNAKE_CASE`

### File Organization

```
agent_name/
├── agent.yml                    # Main manifest
├── agents/                      # Sub-agents
│   └── sub_agent/
│       └── agent.yml
├── tools/                       # Specialized tools
│   └── tool_name/
│       ├── tool.yml
│       └── scripts/
├── relics/                      # Specialized relics
│   └── relic_name/
│       ├── relic.yml
│       └── workflows/
├── workflows/                   # Workflows
│   └── workflow_name.workflow.yml
└── system-prompts/              # Persona files
    ├── agent.md
    └── user.md
```

### Versioning

- Use semantic versioning: `"MAJOR.MINOR.PATCH"`
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

### State Management

| State | Meaning | When to Use |
|-------|---------|-------------|
| `stable` | Production-ready | Tested and reliable |
| `unstable` | Under development | Testing phase |
| `deprecated` | Being phased out | Migration in progress |

### Documentation

- Always include detailed `description`
- Add meaningful `summary`
- Use `tags` for categorization
- Include `examples` for tools
- Document complex `parameters_schema`

### Testing

1. Validate manifest syntax
2. Test with minimal imports
3. Add complexity incrementally
4. Test error conditions
5. Verify hot-reload behavior

---

## Examples

### Complete Examples in Repository

**Simple Agent:**
- `manifests/agents/journaler/agent.yml`

**Hierarchical Agent:**
- `manifests/agents/research_orchestrator/agent.yml`
- With sub-agents, tools, relics, workflows

**Enhanced Tool:**
- `manifests/tools/sentiment_analyzer/tool.yml`

**Workflows:**
- `manifests/workflow/simple_data_processing.workflow.yml`
- `manifests/workflow/journal_entry_pipeline.workflow.yml`
- `manifests/workflow/multi_agent_research.workflow.yml`

**Relic with Workflows:**
- `manifests/agents/research_orchestrator/relics/research_cache/relic.yml`

### Quick Reference Cards

**Minimal Agent:**
```yaml
kind: Agent
version: "1.0"
name: "my_agent"
summary: "Description"
author: "YOUR_NAME"
state: "stable"
persona:
  agent: "./prompts/agent.md"
agency_level: "default"
grade: "common"
iteration_cap: 10
cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"
import:
  tools:
    - "file_system"
```

**Minimal Tool:**
```yaml
kind: Tool
version: "1.0"
name: "my_tool"
summary: "Description"
author: "YOUR_NAME"
state: "stable"
execution:
  type: "script"
  runtime: "python3"
  entrypoint: "./script.py"
parameters_schema:
  type: "object"
  required: ["input"]
  properties:
    input:
      type: "string"
```

**Minimal Workflow:**
```yaml
kind: Workflow
version: "1.0"
name: "my_workflow"
summary: "Description"
author: "YOUR_NAME"
state: "stable"
trigger:
  type: "manual"
  parameters:
    input: "string"
steps:
  - name: "step1"
    type: "tool"
    target: "my_tool"
    parameters:
      input: "$(trigger.input)"
configuration:
  timeout: 300
import:
  tools:
    - "my_tool"
```

---

## Additional Resources

- **[WORKFLOW_DESIGN.md](./WORKFLOW_DESIGN.md)** - Workflow-specific design details
- **[FRACTAL_DESIGN.md](./FRACTAL_DESIGN.md)** - Import philosophy and patterns
- **[README.md](../README.md)** - Project overview and quick start
- **[ROADMAP.md](./ROADMAP.md)** - Development roadmap

---

**"Declarative reality, sovereign entities, fractal composition."** 🏛️
