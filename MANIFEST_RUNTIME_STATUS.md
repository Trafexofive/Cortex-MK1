# Manifest Ingestion & Runtime Executor: Current Architecture

## Overview

The **manifest_ingestion** and **runtime_executor** services work together to provide a declarative, manifest-driven execution environment for agents, tools, and workflows in Cortex-Prime.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     MANIFEST LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

1. MANIFEST FILES (YAML)
   └─ manifests/
      ├─ agents/
      │  ├─ research_orchestrator/agent.yml
      │  └─ journaler/agent.yml
      ├─ tools/
      └─ relics/

                    ↓

2. HOT-RELOAD WATCHER (manifest_ingestion)
   └─ Detects file changes (created/modified/deleted)
   └─ Triggers reload_manifest_file()

                    ↓

3. MANIFEST PARSER (manifest_ingestion)
   └─ Parses YAML content
   └─ Resolves context variables ($AGENT_NAME, $TIMESTAMP, etc.)
   └─ Validates against Pydantic models

                    ↓

4. MANIFEST REGISTRY (manifest_ingestion)
   └─ In-memory storage by type:
      ├─ registry.agents[name] = AgentManifest
      ├─ registry.tools[name] = ToolManifest
      ├─ registry.relics[name] = RelicManifest
      └─ registry.workflows[name] = WorkflowManifest
   └─ Validates dependencies (imports)

                    ↓

5. RUNTIME EXECUTOR REQUESTS
   └─ Fetches manifest via HTTP: GET /registry/manifest/{type}/{name}
   └─ Executes based on manifest specification
```

## Current Implementation

### Manifest Ingestion Service (Port 8082)

**Responsibilities:**
- Parse YAML manifests with embedded markdown
- Validate manifest structure using Pydantic models
- Maintain in-memory registry of all loaded manifests
- Hot-reload manifests when files change
- Resolve context variables dynamically
- Validate inter-manifest dependencies
- Serve manifests to other services via REST API

**Key Components:**

1. **ManifestParser** (`parsers/manifest_parser.py`)
   - Parses YAML and Markdown content
   - Resolves context variables like `$TIMESTAMP`, `$AGENT_NAME`
   - Supports both pure YAML and Markdown with frontmatter

2. **ManifestRegistryService** (`registry/manifest_registry.py`)
   - In-memory storage organized by manifest type
   - Dependency validation and resolution
   - Lifecycle management (create, update, delete)

3. **HotReloadWatcher** (`hotreload.py`)
   - Filesystem watcher for manifest changes
   - Debounced reload to avoid excessive parsing
   - Handles create, modify, and delete events

4. **Context Variable Resolver** (`context_variables.py`)
   - Dynamic variable resolution at runtime
   - 22 built-in resolvers (timestamp, agent name, session ID, etc.)
   - Extensible resolver system

**API Endpoints:**
```
GET  /health                              - Service health
GET  /registry/status                     - Registry statistics
POST /manifests/parse                     - Parse manifest content
POST /manifests/upload                    - Upload manifest file
GET  /registry/agents                     - List all agents
GET  /registry/tools                      - List all tools
GET  /registry/relics                     - List all relics
GET  /registry/manifest/{type}/{name}     - Get specific manifest
GET  /registry/dependencies/{type}/{name} - Get dependencies
POST /registry/sync                       - Force filesystem sync
```

**Current State:**
```bash
curl http://localhost:8082/registry/status
{
  "total_manifests": 0,  # ⚠️ ISSUE: Auto-load not working
  "by_type": {
    "agents": 0,
    "tools": 0,
    "relics": 0,
    "workflows": 0
  },
  "last_updated": "2025-10-09T12:35:13.325930",
  "manifests_root": "/manifests"
}
```

### Runtime Executor Service (Port 8083)

**Responsibilities:**
- Execute tools, agents, and workflows
- Fetch manifests from ingestion service
- Sandboxed execution with resource limits
- Track execution history and statistics
- Multiple runtime types (Python, Shell, Docker)

**Key Components:**

1. **Execution Registry** (`registry/execution_registry.py`)
   - Tracks all executions with metadata
   - Execution lifecycle management
   - Performance statistics

2. **Executors** (`executors/`)
   - **PythonExecutor** - Secure Python script execution
   - **ShellExecutor** - Bash script execution
   - **DockerExecutor** - Containerized execution
   - Base class with resource limiting

3. **Execution Flow:**
   ```python
   # 1. Fetch manifest from ingestion service
   manifest = await _fetch_manifest("Agent", "research_orchestrator")
   
   # 2. Create execution request
   request = ExecutionRequest(
       entity_type="agent",
       entity_name="research_orchestrator",
       parameters=input_data,
       manifest_data=manifest
   )
   
   # 3. Determine runtime type from manifest
   runtime_type = await _determine_runtime_type(manifest)
   
   # 4. Get appropriate executor
   executor = app.state.executors[runtime_type]
   
   # 5. Execute with sandboxing
   result = await executor.execute(request)
   ```

**API Endpoints:**
```
GET  /health                          - Service health
GET  /executors                       - List available executors
POST /execute/tool                    - Execute a tool by name
POST /execute/agent                   - Execute an agent
POST /execute/workflow                - Execute a workflow
POST /execute/direct                  - Direct execution with full request
GET  /executions                      - List execution history
GET  /executions/{id}                 - Get execution details
POST /executions/{id}/cancel          - Cancel running execution
```

## Issues Identified

### 1. ⚠️ Auto-Load Not Working

**Problem:** Manifests defined in `manifests/autoload.yml` are not being loaded into the registry.

**Evidence:**
```bash
curl http://localhost:8082/registry/status
# Shows: "total_manifests": 0
```

**Root Cause Investigation Needed:**
- Volume mounting: `./manifests:/app/manifests:ro` (from host `infra/`)
- Path resolution: autoload.yml expects `/app/manifests/autoload.yml`
- Relative paths in autoload.yml use `../test_against_manifest/`

**Possible Issues:**
1. Volume mount path mismatch (infra/manifests vs project root manifests)
2. Autoload file not found at expected location
3. Relative path resolution failing
4. Silent failure in auto_load_manifests()

### 2. ⚠️ CLI Loads Manifests Directly

**Current Behavior:**
The CLI bypasses the auto-load mechanism by:
1. Reading manifest file from local filesystem
2. POSTing content to `/manifests/parse` endpoint
3. Getting back parsed manifest
4. Using manifest directly with LLM gateway

**Implication:**
- CLI works even though auto-load is broken
- No dependency resolution for imported agents/tools/relics
- No centralized registry of loaded manifests
- Each client re-parses manifests

### 3. ⚠️ Dependency Resolution Not Active

**Problem:** Manifests with `import:` sections are not automatically loading dependencies.

**Example:**
```yaml
# research_orchestrator/agent.yml
import:
  agents:
    - "./agents/web_researcher/agent.yml"  # Not auto-loaded
  tools:
    - "./tools/pdf_extractor/tool.yml"     # Not auto-loaded
  relics:
    - "./relics/research_cache/relic.yml"  # Not auto-loaded
```

**Impact:**
- Complex manifests can't leverage sub-agents
- No fractal composition in practice
- Tool/agent orchestration broken

## How It Should Work

### Correct Flow

```
1. SERVICE STARTUP
   ├─ Load manifests/autoload.yml
   ├─ Parse each manifest listed
   ├─ Resolve imports (recursive)
   │  ├─ Load web_researcher agent
   │  ├─ Load pdf_extractor tool
   │  └─ Load research_cache relic
   ├─ Validate dependencies
   └─ Store in registry

2. HOT-RELOAD (Runtime)
   ├─ Detect: research_orchestrator/agent.yml modified
   ├─ Re-parse manifest
   ├─ Re-resolve imports
   ├─ Update registry
   └─ Notify dependent services

3. EXECUTION REQUEST
   ├─ Runtime executor requests manifest
   ├─ GET /registry/manifest/Agent/research_orchestrator
   ├─ Returns complete manifest with resolved imports
   ├─ Execute with all dependencies available
   └─ Track execution in registry
```

### Expected Registry State

```json
{
  "total_manifests": 8,
  "by_type": {
    "agents": 2,      // research_orchestrator, web_researcher
    "tools": 3,       // pdf_extractor, web_scraper, html_parser
    "relics": 1,      // research_cache
    "workflows": 2    // multi_agent_research, cache_cleanup
  }
}
```

## Next Steps

### Priority 1: Fix Auto-Load

1. **Investigate Volume Mounts**
   ```bash
   docker exec cortex-prime_manifest_ingestion_mk1 ls -la /app/manifests/
   docker exec cortex-prime_manifest_ingestion_mk1 cat /app/manifests/autoload.yml
   ```

2. **Check Logs**
   ```bash
   docker logs cortex-prime_manifest_ingestion_mk1 | grep -i "auto-load\|error"
   ```

3. **Fix Path Resolution**
   - Ensure autoload.yml exists at `/app/manifests/autoload.yml`
   - Update relative paths to use correct base directory
   - Add error logging for failed loads

### Priority 2: Implement Dependency Resolution

1. **Update ManifestRegistryService**
   - When loading a manifest, recursively load imports
   - Track dependency graph
   - Detect circular dependencies

2. **Update Auto-Load Logic**
   - Load dependencies before dependent manifests
   - Validate all imports are resolved
   - Fail fast on missing dependencies (or skip if configured)

### Priority 3: Enhance CLI

1. **Use Registry Instead of Direct Parse**
   - POST manifest to `/manifests/upload` to register it
   - GET manifest from `/registry/manifest/{type}/{name}`
   - Leverage resolved dependencies

2. **Show Dependency Tree**
   - Display imported agents, tools, relics
   - Indicate which are available vs missing

## Summary

**What Works:**
✅ CLI loads and parses individual manifests
✅ LLM gateway integration with streaming
✅ Manifest parsing with context variables
✅ Hot-reload file watching
✅ Runtime executor with sandboxing
✅ Beautiful terminal UI

**What's Broken:**
❌ Auto-load mechanism not populating registry
❌ Dependency resolution not active
❌ Fractal composition not working
❌ Registry shows 0 manifests despite autoload.yml

**Impact:**
- CLI works but doesn't leverage full manifest system
- Complex manifests with imports are partially functional
- Services can't discover available agents/tools
- Orchestration between agents/tools/relics not possible

**Root Cause:**
Likely a volume mounting or path resolution issue preventing autoload.yml from being found or properly parsed during service startup.
