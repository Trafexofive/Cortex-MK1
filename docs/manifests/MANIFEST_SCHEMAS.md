# Manifest Schema Documentation

**Cortex-Prime MK1 v1.0 Sovereign Core Standard**

Complete schema reference for all manifest types in the Cortex-Prime MK1 ecosystem.

---

## Table of Contents

1. [Common Fields](#common-fields)
2. [Tool Manifest Schema](#tool-manifest-schema)
3. [Relic Manifest Schema](#relic-manifest-schema)
4. [Agent Manifest Schema](#agent-manifest-schema)
5. [Workflow Manifest Schema](#workflow-manifest-schema)
6. [Monument Manifest Schema](#monument-manifest-schema)
7. [Amulet Manifest Schema](#amulet-manifest-schema)
8. [Data Types Reference](#data-types-reference)
9. [Import Patterns](#import-patterns)
10. [Examples](#examples)

---

## Common Fields

All manifests share these required base fields:

```yaml
kind: string                    # REQUIRED: Manifest type (Tool|Relic|Agent|Workflow|Monument|Amulet)
version: string                 # REQUIRED: Manifest schema version (e.g., "1.0")
name: string                    # REQUIRED: Unique identifier (lowercase, alphanumeric, hyphens/underscores)
summary: string                 # REQUIRED: Brief one-line description
author: string                  # REQUIRED: Creator identifier
state: string                   # REQUIRED: Lifecycle state (stable|unstable|experimental|deprecated)
description: string             # OPTIONAL: Detailed multi-line description
tags: array<string>             # OPTIONAL: Searchable tags
metadata: object                # OPTIONAL: Custom metadata fields
```

### Field Constraints

- **kind**: Must be one of: `Tool`, `Relic`, `Agent`, `Workflow`, `Monument`, `Amulet`
- **version**: Semantic versioning recommended (e.g., "1.0", "2.1.3")
- **name**: Must be unique within scope, lowercase recommended
- **state**: 
  - `stable` - Production ready
  - `unstable` - Functional but may change
  - `experimental` - Testing/development only
  - `deprecated` - Scheduled for removal
- **tags**: Used for discovery and categorization

---

## Tool Manifest Schema

Tools are executable functions/scripts that agents can invoke.

### Complete Schema

```yaml
# ===== REQUIRED FIELDS =====
kind: Tool
version: string
name: string
summary: string
author: string
state: string

# ===== CORE FIELDS =====
description: string             # Detailed description
returns: string                 # Description of return value/structure

# ===== IMPLEMENTATION =====
implementation:
  type: string                  # REQUIRED: "script" | "container" | "api" | "binary"
  runtime: string               # Runtime environment (e.g., "python3", "node", "go")
  entrypoint: string            # REQUIRED: Path to executable/script
  
  # Optional implementation fields
  resources:
    memory: string              # Memory limit (e.g., "128M", "1G")
    cpu: string                 # CPU limit (e.g., "0.5", "2")
    timeout: integer            # Timeout in seconds
    disk: string                # Disk space (e.g., "100M")
  
  build:
    engine: string              # Build system (e.g., "pip", "npm", "docker")
    requirements_file: string   # Dependencies file path
    build_command: string       # Custom build command
    build_args: object          # Build arguments
  
  health_check:
    type: string                # "script" | "api_request" | "none"
    command: string             # Health check command
    expected_exit_code: integer # Expected exit code (default: 0)
    expected_output_contains: string  # Expected output substring
    endpoint: string            # For API health checks
    interval: integer           # Check interval in seconds

# ===== PARAMETERS =====
parameters:
  - name: string                # REQUIRED: Parameter name
    type: string                # REQUIRED: Data type (string|number|boolean|object|array)
    description: string         # Parameter description
    required: boolean           # Is parameter required? (default: false)
    default: any                # Default value
    enum: array                 # Allowed values (for enums)
    validation:                 # Optional validation rules
      min: number               # Minimum value (for numbers)
      max: number               # Maximum value (for numbers)
      pattern: string           # Regex pattern (for strings)
      min_length: integer       # Min string length
      max_length: integer       # Max string length

# ===== ENVIRONMENT =====
environment:
  variables: object             # Environment variables (key-value pairs)
  secrets: array<string>        # Required secrets (from environment/vault)

# ===== METADATA =====
tags: array<string>
metadata: object                # Custom metadata

# ===== EXAMPLES =====
examples:
  - description: string
    input: object
    output: object
```

### Tool Types

**Script-based:**
```yaml
implementation:
  type: "script"
  runtime: "python3"
  entrypoint: "./scripts/tool.py"
```

**Container-based:**
```yaml
implementation:
  type: "container"
  runtime: "docker"
  entrypoint: "docker run tool-image"
  build:
    engine: "docker"
    dockerfile: "./Dockerfile"
```

**API-based:**
```yaml
implementation:
  type: "api"
  entrypoint: "https://api.example.com/tool"
  health_check:
    type: "api_request"
    endpoint: "/health"
```

---

## Relic Manifest Schema

Relics are persistent services (databases, APIs, caches, etc.).

### Complete Schema

```yaml
# ===== REQUIRED FIELDS =====
kind: Relic
version: string
name: string
summary: string
author: string
state: string

# ===== CORE FIELDS =====
description: string
service_type: string            # Type of service (cache|database|api|queue|storage|compute)

# ===== INTERFACE =====
interface:
  type: string                  # REQUIRED: "rest_api" | "grpc" | "graphql" | "websocket" | "database"
  base_url: string              # Base URL (supports env vars: ${VAR:-default})
  protocol: string              # Protocol version/spec
  
  # For API-based relics
  endpoints:
    - name: string              # Endpoint identifier
      method: string            # HTTP method (GET|POST|PUT|DELETE|PATCH)
      path: string              # URL path
      description: string       # Endpoint description
      parameters: object        # Parameter definitions (similar to tool parameters)
      request_body: object      # Request body schema
      response: object          # Response schema
      auth_required: boolean    # Requires authentication
  
  # For database relics
  connection:
    type: string                # Database type (postgres|mysql|mongodb|redis)
    host: string
    port: integer
    database: string
    schema: string
  
  # Authentication
  authentication:
    type: string                # "none" | "api_key" | "bearer" | "basic" | "oauth2"
    location: string            # "header" | "query" | "body"
    key_name: string            # Auth key name

# ===== HEALTH CHECK =====
health_check:
  type: string                  # REQUIRED: "api_request" | "tcp_socket" | "command"
  endpoint: string              # Health check endpoint/path
  method: string                # HTTP method (for API)
  expected_status: integer      # Expected status code (default: 200)
  timeout: integer              # Timeout in seconds (default: 10)
  interval: integer             # Check interval in seconds (default: 30)
  retries: integer              # Number of retries (default: 3)
  command: string               # Command for command-based checks

# ===== PERSISTENCE =====
persistence:
  type: string                  # "none" | "persistent_volume" | "database" | "s3" | "ephemeral"
  size: string                  # Storage size (e.g., "5Gi", "100GB")
  mount_path: string            # Container mount path
  storage_class: string         # Storage class name
  backup:
    enabled: boolean
    schedule: string            # Cron schedule
    retention: string           # Retention period

# ===== DEPLOYMENT =====
deployment:
  type: string                  # REQUIRED: "docker" | "kubernetes" | "docker-compose" | "systemd"
  docker_compose_file: string   # Path to docker-compose.yml
  dockerfile: string            # Path to Dockerfile
  image: string                 # Pre-built image name
  replicas: integer             # Number of replicas (default: 1)
  
  ports:
    - name: string
      port: integer
      target_port: integer
      protocol: string          # TCP|UDP
  
  volumes:
    - name: string
      mount_path: string
      type: string              # persistent|ephemeral|config
  
  resources:
    requests:
      cpu: string
      memory: string
      storage: string
    limits:
      cpu: string
      memory: string
      storage: string
  
  scaling:
    min_replicas: integer
    max_replicas: integer
    metrics:
      - type: string            # cpu|memory|custom
        target_value: string

# ===== ENVIRONMENT =====
environment:
  variables: object             # Environment variables
  secrets: array<string>        # Required secrets
  config_files:
    - path: string
      content: string
      from_secret: boolean

# ===== DEPENDENCIES =====
dependencies:
  services: array<string>       # Other services this depends on
  initialization_order: integer # Startup order

# ===== MONITORING =====
monitoring:
  metrics:
    enabled: boolean
    endpoint: string            # Metrics endpoint (e.g., /metrics)
    format: string              # prometheus|statsd|json
  
  logging:
    level: string               # DEBUG|INFO|WARN|ERROR
    format: string              # json|text
    destination: string         # stdout|file|syslog
  
  tracing:
    enabled: boolean
    provider: string            # jaeger|zipkin|opentelemetry

# ===== METADATA =====
tags: array<string>
metadata: object
```

### Relic Service Types

- **cache**: Redis, Memcached, in-memory caches
- **database**: PostgreSQL, MySQL, MongoDB, etc.
- **api**: REST APIs, GraphQL services
- **queue**: RabbitMQ, Kafka, Redis queues
- **storage**: S3, MinIO, file storage
- **compute**: Background workers, processors

---

## Agent Manifest Schema

Agents are AI entities that can reason, use tools, and delegate to sub-agents.

### Complete Schema

```yaml
# ===== REQUIRED FIELDS =====
kind: Agent
version: string
name: string
summary: string
author: string
state: string

# ===== CORE FIELDS =====
description: string

# ===== PERSONA =====
persona:
  agent: string                 # REQUIRED: Path to agent system prompt
  user: string                  # Optional: Path to user-facing prompt
  examples: array<string>       # Optional: Example conversation files

# ===== AGENCY & CAPABILITIES =====
agency_level: string            # REQUIRED: "default" | "elevated" | "admin" | "restricted"
grade: string                   # REQUIRED: "common" | "rare" | "epic" | "legendary"
iteration_cap: integer          # REQUIRED: Max reasoning iterations (default: 10)

# ===== COGNITIVE ENGINE =====
cognitive_engine:
  primary:
    provider: string            # REQUIRED: LLM provider (google|openai|anthropic|ollama|custom)
    model: string               # REQUIRED: Model identifier
    endpoint: string            # Optional: Custom endpoint
  
  fallback:                     # Optional: Fallback model if primary fails
    provider: string
    model: string
    endpoint: string
  
  parameters:
    temperature: float          # 0.0-2.0, controls randomness
    top_p: float                # 0.0-1.0, nucleus sampling
    top_k: integer              # Top-k sampling
    max_tokens: integer         # Maximum output tokens
    stream: boolean             # Enable streaming responses
    stop_sequences: array<string>  # Stop generation sequences
    presence_penalty: float     # -2.0 to 2.0
    frequency_penalty: float    # -2.0 to 2.0
    seed: integer               # For reproducible outputs
    
  vision:                       # Optional: Vision capabilities
    enabled: boolean
    max_images: integer
    supported_formats: array<string>
  
  function_calling:             # Optional: Function calling config
    mode: string                # "auto" | "none" | "required"
    parallel: boolean           # Allow parallel function calls

# ===== IMPORTS =====
import:
  agents: array<string>         # Paths to sub-agent manifests
  tools: array<string>          # Paths to tool manifests
  relics: array<string>         # Paths to relic manifests
  workflows: array<string>      # Paths to workflow manifests
  amulets: array<string>        # Paths to amulet manifests

# ===== CONTEXT FEEDS =====
context_feeds:
  - id: string                  # REQUIRED: Unique feed identifier
    type: string                # REQUIRED: "on_demand" | "periodic" | "event_driven"
    interval: integer           # For periodic: interval in seconds
    source:
      type: string              # REQUIRED: "tool" | "relic" | "agent" | "internal" | "external"
      name: string              # Source component name
      action: string            # Action/method to invoke
      params: object            # Parameters for the action
    
    transformation:             # Optional: Transform feed data
      type: string              # "jq" | "jsonpath" | "javascript"
      expression: string        # Transformation expression
    
    cache:
      enabled: boolean
      ttl: integer              # Cache TTL in seconds
    
    error_handling:
      on_error: string          # "skip" | "use_cached" | "use_default"
      default_value: any

# ===== MEMORY & STATE =====
memory:
  enabled: boolean              # Enable agent memory
  type: string                  # "conversation" | "semantic" | "episodic" | "hybrid"
  
  conversation:
    max_turns: integer          # Max conversation turns to retain
    summarize_after: integer    # Summarize after N turns
  
  semantic:
    embedding_model: string     # Embedding model for semantic memory
    vector_store: string        # Vector store backend
    max_entries: integer        # Max memory entries
  
  persistence:
    enabled: boolean
    backend: string             # "file" | "database" | "redis"
    path: string                # Storage path/connection

# ===== TOOL USE =====
tool_use:
  mode: string                  # "auto" | "manual" | "disabled"
  max_iterations: integer       # Max tool use iterations
  parallel_execution: boolean   # Allow parallel tool calls
  retry_policy:
    max_attempts: integer
    backoff: string             # "linear" | "exponential"
  
  filters:                      # Tool filtering rules
    allow: array<string>        # Allowed tool names/patterns
    deny: array<string>         # Denied tool names/patterns
  
  validation:
    validate_inputs: boolean    # Validate tool inputs before execution
    validate_outputs: boolean   # Validate tool outputs

# ===== DELEGATION =====
delegation:
  enabled: boolean              # Allow delegation to sub-agents
  max_depth: integer            # Max delegation depth
  strategy: string              # "round_robin" | "capability_match" | "load_balanced"
  
  policies:
    - condition: string         # Delegation condition (expression)
      target_agent: string      # Which sub-agent to delegate to
      priority: integer         # Policy priority

# ===== ENVIRONMENT =====
environment:
  variables: object             # Environment variables
  secrets: array<string>        # Required secrets
  
  resources:
    requests:
      cpu: string
      memory: string
      gpu: string               # Optional: GPU resources
    limits:
      cpu: string
      memory: string
      gpu: string
  
  workspace:
    path: string                # Agent workspace directory
    ephemeral: boolean          # Clean up on exit
    max_size: string            # Max workspace size

# ===== SAFETY & GUARDRAILS =====
safety:
  content_filtering:
    enabled: boolean
    levels: array<string>       # Filtering levels to apply
  
  rate_limiting:
    enabled: boolean
    requests_per_minute: integer
    tokens_per_minute: integer
  
  output_validation:
    enabled: boolean
    max_length: integer
    forbidden_patterns: array<string>
  
  sandboxing:
    enabled: boolean
    isolation_level: string     # "none" | "process" | "container"

# ===== METRICS & OBSERVABILITY =====
metrics:
  track_llm_calls: boolean
  track_tool_usage: boolean
  track_token_usage: boolean
  track_latency: boolean
  track_errors: boolean
  
  custom_metrics:
    - name: string
      type: string              # "counter" | "gauge" | "histogram"
      description: string
      labels: array<string>

# ===== ERROR HANDLING =====
error_handling:
  on_tool_error: string         # "retry" | "skip" | "abort" | "ask_user"
  on_llm_error: string          # "retry" | "fallback" | "abort"
  max_retries: integer
  retry_delay: integer          # Delay between retries (seconds)

# ===== METADATA =====
tags: array<string>
metadata: object
```

### Agent Grades

- **common**: Basic capabilities, limited resources
- **rare**: Enhanced capabilities, moderate resources
- **epic**: Advanced capabilities, significant resources
- **legendary**: Maximum capabilities, premium resources

### Agency Levels

- **restricted**: Limited permissions, supervised
- **default**: Standard permissions
- **elevated**: Enhanced permissions, can delegate
- **admin**: Full permissions, system access

---

## Workflow Manifest Schema

Workflows orchestrate sequences of tool/relic operations.

### Complete Schema

```yaml
# ===== REQUIRED FIELDS =====
kind: Workflow
version: string
name: string
summary: string
author: string
state: string

# ===== CORE FIELDS =====
description: string

# ===== TRIGGER =====
trigger:
  type: string                  # REQUIRED: "manual" | "scheduled" | "event" | "webhook"
  
  # For manual triggers
  parameters: object            # Input parameters (similar to tool parameters)
  
  # For scheduled triggers
  schedule: string              # Cron expression (e.g., "0 0 * * *")
  timezone: string              # Timezone (e.g., "America/New_York")
  
  # For event triggers
  event_source: string          # Event source identifier
  event_type: string            # Event type to listen for
  filter: string                # Event filter expression
  
  # For webhook triggers
  webhook_path: string          # Webhook URL path
  method: string                # HTTP method
  authentication: object        # Webhook auth config

# ===== STEPS =====
steps:
  - name: string                # REQUIRED: Unique step identifier
    type: string                # REQUIRED: "tool" | "relic" | "agent" | "workflow" | "conditional" | "parallel"
    
    # For tool/relic/agent/workflow steps
    target: string              # Target component name
    action: string              # Action/method to invoke (for relics)
    
    parameters: object          # Step parameters (supports variables: $(var.path))
    
    # Control flow
    condition: string           # Execute if condition is true (expression)
    depends_on: array<string>   # Step dependencies
    timeout: integer            # Step timeout in seconds
    
    # Error handling
    on_failure: string          # "abort" | "continue" | "retry" | "skip"
    retry_policy:
      max_attempts: integer
      backoff: string           # "linear" | "exponential"
      delay: integer            # Initial delay in seconds
    
    # Output handling
    output_mapping:             # Map step outputs to variables
      variable_name: string     # Source path in step output
    
    # For conditional steps
    if: string                  # Condition expression
    then: array<step>           # Steps to execute if true
    else: array<step>           # Steps to execute if false
    
    # For parallel steps
    parallel: array<step>       # Steps to execute in parallel
    max_concurrency: integer    # Max parallel executions
    fail_fast: boolean          # Abort on first failure

# ===== CONFIGURATION =====
configuration:
  timeout: integer              # Overall workflow timeout (seconds)
  max_retries: integer          # Default max retries for steps
  
  default_retry_policy:
    max_attempts: integer
    backoff: string
    delay: integer
  
  error_handling:
    on_step_failure: string     # "abort" | "continue" | "rollback"
    rollback_on_failure: boolean
  
  concurrency:
    max_parallel_steps: integer
    resource_limits:
      cpu: string
      memory: string
  
  observability:
    log_level: string           # DEBUG|INFO|WARN|ERROR
    trace_enabled: boolean
    metrics_enabled: boolean
    audit_log: boolean

# ===== OUTPUTS =====
outputs:
  output_name:
    source: string              # Path to output value (e.g., "steps.step1.result")
    description: string
    type: string                # Data type
    required: boolean

# ===== IMPORTS =====
import:
  tools: array<string>
  relics: array<string>
  agents: array<string>
  workflows: array<string>

# ===== VARIABLES =====
variables:                      # Workflow-level variables
  variable_name:
    type: string
    default: any
    description: string

# ===== ERROR HANDLING =====
error_handlers:
  - error_type: string          # Error type or pattern
    handler: string             # Handler step name
    action: string              # "retry" | "skip" | "abort" | "notify"

# ===== NOTIFICATIONS =====
notifications:
  on_start:
    enabled: boolean
    channels: array<string>
  
  on_success:
    enabled: boolean
    channels: array<string>
    message: string
  
  on_failure:
    enabled: boolean
    channels: array<string>
    message: string

# ===== METADATA =====
tags: array<string>
metadata: object
```

### Workflow Step Types

**Tool Execution:**
```yaml
- name: "process_data"
  type: "tool"
  target: "text_analyzer"
  parameters:
    operation: "analyze"
    text: "$(trigger.input)"
```

**Relic Interaction:**
```yaml
- name: "store_result"
  type: "relic"
  target: "kv_store"
  action: "set_value"
  parameters:
    key: "result_$(timestamp)"
    value: "$(steps.process_data.output)"
```

**Agent Delegation:**
```yaml
- name: "ask_agent"
  type: "agent"
  target: "assistant"
  parameters:
    prompt: "Analyze this data"
    context: "$(steps.process_data.output)"
```

**Conditional Execution:**
```yaml
- name: "check_quality"
  type: "conditional"
  if: "$(steps.process_data.score) > 0.8"
  then:
    - name: "approve"
      type: "tool"
      target: "approver"
  else:
    - name: "reject"
      type: "tool"
      target: "rejector"
```

**Parallel Execution:**
```yaml
- name: "parallel_processing"
  type: "parallel"
  parallel:
    - name: "task1"
      type: "tool"
      target: "processor1"
    - name: "task2"
      type: "tool"
      target: "processor2"
  max_concurrency: 2
```

---

## Monument Manifest Schema

Monuments are complete autonomous systems (Infrastructure + Intelligence + Automation).

### Complete Schema

```yaml
# ===== REQUIRED FIELDS =====
kind: Monument
version: string
name: string
summary: string
author: string
state: string

# ===== CORE FIELDS =====
description: string

# ===== INFRASTRUCTURE STACK (Relics) =====
infrastructure:
  relics:
    - name: string              # REQUIRED: Unique relic name
      type: string              # Relic type/category
      path: string              # REQUIRED: Path to relic manifest
      required: boolean         # Is this relic required? (default: true)
      
      config: object            # Relic-specific configuration
      
      scaling:
        min_replicas: integer
        max_replicas: integer
        auto_scale: boolean
      
      health_check:
        enabled: boolean
        interval: integer
        timeout: integer
      
      depends_on: array<string> # Dependencies on other relics

# ===== INTELLIGENCE LAYER (Agents) =====
intelligence:
  agents:
    - name: string              # REQUIRED: Unique agent name
      role: string              # Agent role (orchestrator|worker|assistant|etc)
      path: string              # REQUIRED: Path to agent manifest
      auto_start: boolean       # Auto-start on monument deployment
      instances: integer        # Number of agent instances (default: 1)
      
      config: object            # Agent-specific configuration
      
      delegation:
        can_delegate: boolean
        max_depth: integer
      
      resource_limits:
        cpu: string
        memory: string
        gpu: string

# ===== AUTOMATION LAYER (Workflows) =====
automation:
  workflows:
    - name: string              # REQUIRED: Unique workflow name
      trigger: string           # REQUIRED: Trigger type
      schedule: string          # Cron schedule (for scheduled triggers)
      path: string              # Path to workflow manifest
      
      config: object            # Workflow-specific configuration
      
      enabled: boolean          # Is workflow enabled? (default: true)
      
      dependencies:
        agents: array<string>
        relics: array<string>

# ===== TOOLS INTEGRATION =====
tools:
  - name: string                # Tool identifier
    path: string                # REQUIRED: Path to tool manifest
    purpose: string             # Tool purpose/description
    shared: boolean             # Available to all agents? (default: true)

# ===== DEPLOYMENT =====
deployment:
  type: string                  # REQUIRED: "docker-compose" | "kubernetes" | "terraform" | "ansible"
  compose_file: string          # Path to docker-compose.yml
  kubernetes_manifests: string  # Path to k8s manifests directory
  terraform_module: string      # Path to terraform module
  
  services: array<string>       # Services to deploy
  
  environment: object           # Environment variables
  
  scaling:
    horizontal:
      - service: string
        min: integer
        max: integer
        metric: string          # "cpu" | "memory" | "requests"
        threshold: integer
    
    vertical:
      enabled: boolean
      min_resources: object
      max_resources: object
  
  networking:
    ingress:
      enabled: boolean
      host: string
      tls: boolean
    
    service_mesh:
      enabled: boolean
      provider: string          # "istio" | "linkerd" | "consul"

# ===== MONUMENT INTERFACE =====
interface:
  type: string                  # REQUIRED: "rest_api" | "grpc" | "graphql" | "cli" | "web_ui"
  base_url: string              # Base URL or endpoint
  
  # For API-based interfaces
  endpoints:
    - name: string
      method: string
      path: string
      description: string
      parameters: object
      response: object
      auth_required: boolean
  
  # For CLI interfaces
  commands:
    - name: string
      description: string
      usage: string
      flags: array<object>
  
  # For UI interfaces
  ui:
    type: string                # "web" | "desktop" | "mobile"
    entry_point: string
    assets_path: string

# ===== CONTEXT FEEDS =====
# Monument-level context feeds
context_feeds:
  - id: string
    type: string
    interval: integer
    source: object

# ===== CONFIGURATION =====
config:
  features: array<string>       # Enabled features
  
  limits:
    max_requests: integer
    max_storage: string
    max_compute: string
    concurrent_users: integer
  
  performance:
    target_latency_ms: integer
    target_throughput: integer
    cache_enabled: boolean
  
  security:
    authentication: object
    authorization: object
    encryption: object
    audit_logging: boolean

# ===== OBSERVABILITY =====
observability:
  metrics:
    enabled: boolean
    endpoint: string
    format: string
    retention: string
  
  logging:
    level: string
    structured: boolean
    aggregation: string         # "elasticsearch" | "loki" | "cloudwatch"
  
  tracing:
    enabled: boolean
    provider: string
    sampling_rate: float
  
  health_checks:
    - type: string              # "liveness" | "readiness" | "startup" | "custom"
      path: string
      interval_seconds: integer
      timeout_seconds: integer
      failure_threshold: integer

# ===== DATA MANAGEMENT =====
data:
  persistence:
    - name: string
      type: string              # "database" | "object_store" | "file_system"
      size: string
      backup:
        enabled: boolean
        schedule: string
        retention: string
  
  migrations:
    enabled: boolean
    auto_migrate: boolean
    version: string

# ===== DISASTER RECOVERY =====
disaster_recovery:
  backup:
    enabled: boolean
    schedule: string
    retention_policy: string
  
  restore:
    auto_restore: boolean
    recovery_point_objective: string  # RPO
    recovery_time_objective: string   # RTO

# ===== METADATA =====
tags: array<string>
metadata:
  complexity: string            # "simple" | "complex" | "specialized"
  components_count: integer
  estimated_resource_usage: string
  version: string
  [custom_fields]: any
```

### Monument Complexity Levels

- **simple**: 3-5 components, single-tier architecture, minimal configuration
- **complex**: 10+ components, multi-tier architecture, hierarchical composition
- **specialized**: Domain-specific, custom features, advanced configuration

---

## Amulet Manifest Schema

Amulets are pre-configured packages/templates for quick deployment.

### Complete Schema

```yaml
# ===== REQUIRED FIELDS =====
kind: Amulet
version: string
name: string
summary: string
author: string
state: string

# ===== CORE FIELDS =====
description: string
category: string                # Amulet category (template|preset|plugin|extension)

# ===== TEMPLATE =====
template:
  type: string                  # REQUIRED: "agent" | "workflow" | "monument" | "tool" | "relic"
  base: string                  # Base manifest to extend/template
  
  # Template variables
  variables:
    - name: string              # REQUIRED: Variable name
      type: string              # Variable type
      description: string
      default: any
      required: boolean
      validation: object
  
  # Template files
  files:
    - source: string            # Source file path
      destination: string       # Destination path (supports templating)
      template: boolean         # Is this a template file?

# ===== CONFIGURATION =====
configuration:
  defaults: object              # Default configuration values
  overrides: object             # Configuration overrides
  
  customization:
    prompts:                    # Interactive prompts during installation
      - name: string
        type: string            # "text" | "select" | "confirm" | "password"
        message: string
        default: any
        choices: array          # For select type
    
    hooks:                      # Installation hooks
      pre_install: string       # Script to run before install
      post_install: string      # Script to run after install
      pre_uninstall: string
      post_uninstall: string

# ===== DEPENDENCIES =====
dependencies:
  required:
    tools: array<string>
    relics: array<string>
    agents: array<string>
    amulets: array<string>
  
  optional:
    tools: array<string>
    relics: array<string>
    agents: array<string>

# ===== INSTALLATION =====
installation:
  method: string                # "copy" | "symlink" | "generate"
  target_directory: string
  
  steps:
    - description: string
      command: string
      working_directory: string
      environment: object

# ===== METADATA =====
tags: array<string>
metadata: object

# ===== EXAMPLES =====
examples:
  - name: string
    description: string
    usage: string
    output: string
```

---

## Data Types Reference

### Basic Types

```yaml
string: "text value"
number: 42 | 3.14
boolean: true | false
null: null
```

### Complex Types

```yaml
object:
  key: value
  nested:
    key: value

array:
  - item1
  - item2
  - item3

array<string>:
  - "string1"
  - "string2"
```

### Special Types

```yaml
# Environment variables with defaults
url: "${BASE_URL:-http://localhost:8080}"

# Variable references
value: "$(trigger.input_text)"
nested: "$(steps.step1.output.result)"

# Expressions
condition: "$(steps.process.score) > 0.8"
calculation: "$(steps.calc.a) + $(steps.calc.b)"

# Templates
template: "Processing {{user_name}} at {{timestamp}}"

# Cron expressions
schedule: "0 */6 * * *"  # Every 6 hours
schedule: "0 9 * * MON"  # Every Monday at 9 AM
```

---

## Import Patterns

### Relative Paths

All imports use relative paths from the manifest file:

```yaml
import:
  tools:
    - "./tools/local_tool/tool.yml"              # Local (same directory tree)
    - "../../std/manifests/tools/calculator/"     # External (different tree)
    - "../../../tools/shared/analyzer/"          # Parent directory reference
```

### Import by Type

```yaml
import:
  # Sub-agents
  agents:
    - "./agents/sub_agent/agent.yml"
  
  # Tools
  tools:
    - "./tools/local_tool/tool.yml"
    - "../../shared/tools/calculator/tool.yml"
  
  # Relics
  relics:
    - "./relics/cache/relic.yml"
    - "../../std/manifests/relics/kv_store/relic.yml"
  
  # Workflows
  workflows:
    - "./workflows/cleanup.workflow.yml"
  
  # Amulets
  amulets:
    - "../../amulets/config_preset/amulet.yml"
```

### Monument Imports

Monuments use `path` field for imports:

```yaml
infrastructure:
  relics:
    - name: "storage"
      path: "../../std/manifests/relics/kv_store/relic.yml"

intelligence:
  agents:
    - name: "assistant"
      path: "../../std/manifests/agents/assistant/agent.yml"

automation:
  workflows:
    - name: "pipeline"
      path: "../../std/manifests/workflows/data_pipeline/workflow.yml"
```

---

## Examples

See individual manifest files in:
- `std/manifests/` - Standard library examples
- `testing/test_against_manifest/` - Comprehensive test examples

### Quick Examples

**Minimal Tool:**
```yaml
kind: Tool
version: "1.0"
name: "simple_tool"
summary: "A simple tool"
author: "AUTHOR"
state: "stable"

implementation:
  type: "script"
  runtime: "python3"
  entrypoint: "./script.py"

parameters:
  - name: "input"
    type: "string"
    required: true

tags: ["simple"]
```

**Minimal Relic:**
```yaml
kind: Relic
version: "1.0"
name: "simple_api"
summary: "A simple API"
author: "AUTHOR"
state: "stable"

service_type: "api"

interface:
  type: "rest_api"
  base_url: "http://localhost:8000"

health_check:
  type: "api_request"
  endpoint: "/health"
  expected_status: 200

deployment:
  type: "docker"
  docker_compose_file: "./docker-compose.yml"

tags: ["api"]
```

**Minimal Agent:**
```yaml
kind: Agent
version: "1.0"
name: "simple_agent"
summary: "A simple agent"
author: "AUTHOR"
state: "stable"

persona:
  agent: "./prompt.md"

agency_level: "default"
grade: "common"
iteration_cap: 10

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"

tags: ["simple"]
```

**Minimal Workflow:**
```yaml
kind: Workflow
version: "1.0"
name: "simple_workflow"
summary: "A simple workflow"
author: "AUTHOR"
state: "stable"

trigger:
  type: "manual"

steps:
  - name: "step1"
    type: "tool"
    target: "tool_name"

tags: ["simple"]
```

**Minimal Monument:**
```yaml
kind: Monument
version: "1.0"
name: "simple_monument"
summary: "A simple monument"
author: "AUTHOR"
state: "stable"

infrastructure:
  relics:
    - name: "storage"
      path: "./relics/storage/relic.yml"

intelligence:
  agents:
    - name: "agent"
      path: "./agents/agent/agent.yml"

deployment:
  type: "docker-compose"
  compose_file: "./docker-compose.yml"

interface:
  type: "rest_api"
  base_url: "http://localhost:9000"

tags: ["simple"]
```

---

## Validation

All manifests must:
1. ✅ Be valid YAML
2. ✅ Include all required fields
3. ✅ Use correct field types
4. ✅ Follow naming conventions (lowercase, alphanumeric, hyphens/underscores)
5. ✅ Use relative paths for imports
6. ✅ Include implementation files (tools/relics)
7. ✅ Include system prompts (agents)

---

**Version:** 1.0.0  
**Standard:** Cortex-Prime MK1 v1.0 Sovereign Core Standard  
**Last Updated:** 2025-01-08
