# Manifest Quick Reference

**Fast lookup guide for Cortex-Prime MK1 manifest creation**

## Manifest Types

| Type | Purpose | Key Fields |
|------|---------|------------|
| **Tool** | Executable functions/scripts | `implementation`, `parameters`, `returns` |
| **Relic** | Persistent services (APIs, DBs) | `service_type`, `interface`, `health_check`, `deployment` |
| **Agent** | AI entities with reasoning | `persona`, `cognitive_engine`, `import`, `context_feeds` |
| **Workflow** | Orchestrated task sequences | `trigger`, `steps`, `outputs` |
| **Monument** | Complete autonomous systems | `infrastructure`, `intelligence`, `automation`, `interface` |
| **Amulet** | Pre-configured templates | `template`, `variables`, `installation` |

---

## Required Fields (All Manifests)

```yaml
kind: Tool|Relic|Agent|Workflow|Monument|Amulet
version: "1.0"
name: "unique_name"
summary: "Brief description"
author: "AUTHOR_ID"
state: stable|unstable|experimental|deprecated
```

---

## Tool Quick Template

```yaml
kind: Tool
version: "1.0"
name: "tool_name"
summary: "What the tool does"
author: "YOUR_ID"
state: "stable"

implementation:
  type: "script"           # script|container|api|binary
  runtime: "python3"       # python3|node|go|etc
  entrypoint: "./script.py"

parameters:
  - name: "param_name"
    type: "string"         # string|number|boolean|object|array
    required: true
    description: "Parameter description"

tags: ["category"]
```

---

## Relic Quick Template

```yaml
kind: Relic
version: "1.0"
name: "relic_name"
summary: "What the service provides"
author: "YOUR_ID"
state: "stable"

service_type: "cache"      # cache|database|api|queue|storage

interface:
  type: "rest_api"         # rest_api|grpc|graphql|database
  base_url: "http://localhost:8000"
  endpoints:
    - name: "get_data"
      method: "GET"
      path: "/data"

health_check:
  type: "api_request"
  endpoint: "/health"
  expected_status: 200

deployment:
  type: "docker"
  docker_compose_file: "./docker-compose.yml"

tags: ["category"]
```

---

## Agent Quick Template

```yaml
kind: Agent
version: "1.0"
name: "agent_name"
summary: "Agent purpose"
author: "YOUR_ID"
state: "stable"

persona:
  agent: "./system-prompts/agent.md"

agency_level: "default"    # default|elevated|admin|restricted
grade: "common"            # common|rare|epic|legendary
iteration_cap: 10

cognitive_engine:
  primary:
    provider: "google"     # google|openai|anthropic|ollama
    model: "gemini-1.5-flash"
  parameters:
    temperature: 0.7
    max_tokens: 4096

import:
  tools:
    - "./tools/tool/tool.yml"

tags: ["category"]
```

---

## Workflow Quick Template

```yaml
kind: Workflow
version: "1.0"
name: "workflow_name"
summary: "Workflow purpose"
author: "YOUR_ID"
state: "stable"

trigger:
  type: "manual"           # manual|scheduled|event|webhook
  parameters:
    input:
      type: "string"

steps:
  - name: "step1"
    type: "tool"           # tool|relic|agent|workflow|conditional|parallel
    target: "tool_name"
    parameters:
      param: "$(trigger.input)"

import:
  tools:
    - "../tools/tool/tool.yml"

tags: ["category"]
```

---

## Monument Quick Template

```yaml
kind: Monument
version: "1.0"
name: "monument_name"
summary: "Complete system description"
author: "YOUR_ID"
state: "stable"

infrastructure:
  relics:
    - name: "storage"
      path: "../../std/manifests/relics/kv_store/relic.yml"

intelligence:
  agents:
    - name: "assistant"
      path: "../../std/manifests/agents/assistant/agent.yml"
      auto_start: true

automation:
  workflows:
    - name: "pipeline"
      trigger: "on_demand"
      path: "../../std/manifests/workflows/data_pipeline/workflow.yml"

deployment:
  type: "docker-compose"
  compose_file: "./docker-compose.yml"

interface:
  type: "rest_api"
  base_url: "http://localhost:9000"

tags: ["category"]
```

---

## Common Patterns

### Import Patterns

```yaml
import:
  # Local (same directory tree)
  tools:
    - "./tools/local_tool/tool.yml"
  
  # External (standard library)
  tools:
    - "../../std/manifests/tools/calculator/tool.yml"
  
  # Parent directory
  relics:
    - "../../../relics/shared/kv_store/relic.yml"
```

### Context Feeds

```yaml
context_feeds:
  # From tool (on-demand)
  - id: "current_time"
    type: "on_demand"
    source:
      type: "tool"
      name: "time_tool"
      action: "get_datetime"
  
  # From relic (periodic)
  - id: "cache_stats"
    type: "periodic"
    interval: 60
    source:
      type: "relic"
      name: "cache"
      action: "get_stats"
  
  # From agent
  - id: "agent_status"
    type: "on_demand"
    source:
      type: "agent"
      name: "sub_agent"
      action: "get_status"
```

### Variable References

```yaml
# Trigger inputs
value: "$(trigger.param_name)"

# Step outputs
value: "$(steps.step_name.output_field)"

# Nested paths
value: "$(steps.step1.result.data.value)"

# Environment variables
url: "${API_URL:-http://localhost:8000}"
```

### Workflow Steps

```yaml
steps:
  # Tool execution
  - name: "process"
    type: "tool"
    target: "processor"
    parameters:
      data: "$(trigger.input)"
  
  # Relic interaction
  - name: "store"
    type: "relic"
    target: "storage"
    parameters:
      key: "result"
      value: "$(steps.process.output)"
  
  # Conditional
  - name: "check"
    type: "conditional"
    if: "$(steps.process.success) == true"
    then:
      - name: "success_action"
        type: "tool"
        target: "notifier"
  
  # Parallel
  - name: "parallel_tasks"
    type: "parallel"
    parallel:
      - name: "task1"
        type: "tool"
        target: "tool1"
      - name: "task2"
        type: "tool"
        target: "tool2"
```

---

## Field Types

```yaml
string: "text"
number: 42
float: 3.14
boolean: true
null: null

object:
  key: value
  nested:
    key: value

array:
  - item1
  - item2

array<string>:
  - "string1"
  - "string2"
```

---

## Common Cron Schedules

```yaml
schedule: "* * * * *"        # Every minute
schedule: "0 * * * *"        # Every hour
schedule: "0 0 * * *"        # Daily at midnight
schedule: "0 9 * * *"        # Daily at 9 AM
schedule: "0 9 * * MON"      # Every Monday at 9 AM
schedule: "0 */6 * * *"      # Every 6 hours
schedule: "0 0 1 * *"        # First day of month
schedule: "0 0 * * 0"        # Every Sunday
```

---

## LLM Providers

```yaml
cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"    # or gemini-1.5-pro

    provider: "openai"
    model: "gpt-4"               # or gpt-3.5-turbo

    provider: "anthropic"
    model: "claude-3-opus"       # or claude-3-sonnet

    provider: "ollama"
    model: "llama3.1:8b"         # or llama3.1:70b
```

---

## Resource Specifications

```yaml
resources:
  requests:
    cpu: "0.5"        # 0.5 cores
    memory: "512Mi"   # 512 megabytes
  limits:
    cpu: "2.0"        # 2 cores
    memory: "2Gi"     # 2 gigabytes

# Common sizes
memory: "128Mi"       # Small tool
memory: "512Mi"       # Medium tool/agent
memory: "2Gi"         # Large agent
memory: "8Gi"         # Heavy processing

timeout: 10           # 10 seconds
timeout: 300          # 5 minutes
timeout: 3600         # 1 hour
```

---

## Health Check Examples

**API Health Check:**
```yaml
health_check:
  type: "api_request"
  endpoint: "/health"
  method: "GET"
  expected_status: 200
  timeout: 10
  interval: 30
```

**Script Health Check:**
```yaml
health_check:
  type: "script"
  command: "python3 ./health.py"
  expected_exit_code: 0
  expected_output_contains: '"status": "ok"'
```

**TCP Socket Check:**
```yaml
health_check:
  type: "tcp_socket"
  host: "localhost"
  port: 8000
  timeout: 5
```

---

## Tags Best Practices

```yaml
tags:
  - "category"         # Tool category (math, text, etc)
  - "std"              # Standard library
  - "production"       # Production ready
  - "experimental"     # Experimental feature
  - "v1.0"             # Version tag
  - "nlp"              # Technology/domain
```

---

## File Structure

```
component_name/
├── {tool|relic|agent|workflow|monument}.yml
├── scripts/ or app/
├── system-prompts/     # For agents
├── tests/
├── requirements.txt
├── Dockerfile          # For relics
├── docker-compose.yml  # For relics/monuments
└── README.md
```

---

## Validation Checklist

- [ ] All required fields present
- [ ] Valid YAML syntax
- [ ] Correct `kind` value
- [ ] Unique `name` (lowercase, alphanumeric)
- [ ] Valid `state` value
- [ ] Relative paths in imports
- [ ] Implementation files exist
- [ ] System prompts exist (for agents)
- [ ] Documentation included
- [ ] Tags added

---

## Common Errors

❌ **Absolute paths in imports**
```yaml
import:
  tools:
    - "/absolute/path/tool.yml"  # WRONG
```
✅ **Use relative paths**
```yaml
import:
  tools:
    - "../../tools/tool.yml"     # CORRECT
```

❌ **Missing required fields**
```yaml
kind: Tool
name: "tool"
# Missing: version, summary, author, state
```

❌ **Invalid kind**
```yaml
kind: "tool"  # WRONG - must be capitalized
kind: Tool    # CORRECT
```

❌ **Wrong variable syntax**
```yaml
value: "${steps.process.output}"  # WRONG
value: "$(steps.process.output)"  # CORRECT
```

---

## Quick Start

1. **Choose manifest type** (Tool, Relic, Agent, Workflow, Monument)
2. **Copy template** from this guide
3. **Fill in required fields**
4. **Add implementation** (scripts, configs, etc.)
5. **Test locally**
6. **Validate** against schema
7. **Document** in README.md

---

## Examples Location

- Standard Library: `std/manifests/`
- Test Suite: `testing/test_against_manifest/`
- Full Schema: `docs/MANIFEST_SCHEMAS.md`

---

## Support

For detailed schema documentation, see:
- `docs/MANIFEST_SCHEMAS.md` - Complete schema reference
- `std/manifests/CATALOG.md` - Standard library catalog
- `testing/test_against_manifest/README.md` - Test examples

---

**Version:** 1.0.0  
**Standard:** Cortex-Prime MK1 v1.0 Sovereign Core Standard
