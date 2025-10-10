# Fractal Manifest Design Philosophy

## Core Principle: Universal Composability

**ANY manifest can import ANY other manifest.**

This creates a fractal, tree-structured system where complexity emerges from composition rather than monolithic design.

## Import Philosophy

### 1. Agents can import:
- ✅ Agents (sub-agents, delegation, specialization)
- ✅ Tools (capabilities, actions)
- ✅ Relics (state, memory, persistence)
- ✅ Workflows (orchestration, pipelines)
- ✅ Monuments (external systems)
- ✅ Amulets (behavior modifiers)

### 2. Tools can import:
- ✅ Agents (for intelligent processing)
- ✅ Tools (tool chaining, pipelines)
- ✅ Relics (for state/caching)
- ✅ Workflows (complex operations)

**Example:** `intelligent_pdf_extractor` tool imports `document_parser` agent for complex documents.

### 3. Relics can import:
- ✅ Workflows (automation, cleanup, reindexing)
- ✅ Tools (data processing, transformation)
- ✅ Relics (companion stores, backups)
- ✅ Agents (intelligent data curation)

**Example:** `research_cache` relic imports `cache_cleanup` workflow that runs weekly.

### 4. Workflows can import:
- ✅ Agents (orchestration, delegation)
- ✅ Tools (operations, transformations)
- ✅ Relics (state management)
- ✅ Workflows (nested pipelines, recursion)

**Example:** `cache_cleanup` workflow imports `data_curator` agent and `cache_analyzer` tool.

## Tree Structure

```
research_orchestrator/              (Root Agent)
├── agent.yml                       (Main manifest)
├── agents/                         (Sub-agents)
│   ├── web_researcher/
│   │   ├── agent.yml
│   │   ├── tools/
│   │   ├── workflows/
│   │   └── relics/
│   ├── academic_researcher/
│   ├── data_analyst/
│   ├── synthesis_writer/
│   └── fact_checker/
├── tools/                          (Specialized tools)
│   ├── pdf_extractor/
│   │   ├── tool.yml
│   │   ├── agents/                 (Tool imports agents!)
│   │   │   └── document_parser/
│   │   └── relics/
│   └── citation_formatter/
├── relics/                         (Specialized relics)
│   ├── research_cache/
│   │   ├── relic.yml
│   │   ├── workflows/              (Relic imports workflows!)
│   │   │   ├── cache_cleanup.workflow.yml
│   │   │   └── cache_reindex.workflow.yml
│   │   └── docker-compose.yml
│   ├── citation_db/
│   └── knowledge_graph/
├── workflows/                      (Orchestration workflows)
│   ├── deep_research_pipeline.workflow.yml
│   └── fact_verification.workflow.yml
└── system-prompts/                 (Persona definitions)
```

## Fractal Patterns

### Pattern 1: Hierarchical Agents
```yaml
# Parent Agent
import:
  agents:
    - "./agents/specialist_1/agent.yml"  # Each can have own imports
    - "./agents/specialist_2/agent.yml"
    - "./agents/specialist_3/agent.yml"
```

### Pattern 2: Tool-Agent Symbiosis
```yaml
# Tool Manifest
import:
  agents:
    - "./agents/processor_agent/agent.yml"  # For intelligent processing

delegation:
  to_agent: "processor_agent"
  condition: "complexity > 0.7"
```

### Pattern 3: Relic-Workflow Automation
```yaml
# Relic Manifest
import:
  workflows:
    - "./workflows/cleanup.workflow.yml"
    - "./workflows/optimization.workflow.yml"

automation:
  scheduled_workflows:
    - workflow: "cleanup"
      schedule: "0 0 * * 0"  # Weekly
```

### Pattern 4: Workflow Recursion
```yaml
# Workflow Manifest
import:
  workflows:
    - "self"  # Self-reference for recursion

steps:
  - name: "recursive_call"
    type: "workflow"
    target: "self"
    condition: "depth < max_depth"
```

## Benefits

1. **Modularity**: Each manifest is self-contained yet composable
2. **Reusability**: Share sub-components across multiple parents
3. **Scalability**: Complex systems emerge from simple components
4. **Testability**: Test each component in isolation
5. **Maintainability**: Update one component, affects all importers
6. **Clarity**: Tree structure mirrors logical organization
7. **Flexibility**: Any combination is possible

## Path Resolution

### Relative Paths
```yaml
import:
  agents:
    - "./agents/sub_agent/agent.yml"           # Sibling directory
    - "../../shared/agents/common/agent.yml"   # Parent directory
```

### Absolute Paths (from manifest root)
```yaml
import:
  tools:
    - "tools/global_tool/tool.yml"             # From manifest root
```

### Global References
```yaml
import:
  tools:
    - "file_system"                            # Global tool name
    - "web_scraper"                            # No path = global
```

## Dependency Resolution

The manifest ingestion service:
1. **Parses** manifest
2. **Resolves** all import paths
3. **Recursively loads** dependencies
4. **Validates** circular dependencies
5. **Builds** dependency graph
6. **Checks** all dependencies exist
7. **Registers** in proper order

## API Support

Upload manifests from anywhere:
```bash
# From local filesystem
curl -X POST -F "file=@agent.yml" http://manifest-service:8082/manifests/upload

# From remote host
curl -X POST -F "file=@complex_agent.yml" http://your-server:8082/manifests/upload
```

The service handles:
- Recursive dependency loading
- Path normalization
- Circular dependency detection
- Version compatibility
- Hot-reload of changed manifests

## Examples in This Repo

1. **research_orchestrator** - Complex agent with 5 sub-agents, 3 relics, 2 tools
2. **intelligent_pdf_extractor** - Tool that imports an agent
3. **research_cache** - Relic that imports workflows
4. **cache_cleanup** - Workflow imported by a relic

---

**"Complexity from composition, not monoliths."** 🏛️
