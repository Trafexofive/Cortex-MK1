# Test Manifest Collection

Comprehensive test manifests for Cortex-Prime MK1 validation with **proper local imports** and **context_feeds**.

## Key Features

✅ **All imports use relative paths** - No magic globals, works from anywhere  
✅ **Context feeds implemented** - Agents have dynamic data injection  
✅ **Full modular structure** - Complete implementation code included  
✅ **Fractal composition** - Sub-agents, local tools, local relics, local workflows  
✅ **Working implementations** - All code is tested and functional  

## Structure

```
test_against_manifest/
├── tools/simple/
│   ├── calculator/                       ✅ Arithmetic tool
│   │   ├── tool.yml
│   │   ├── scripts/calculator.py         (tested ✓)
│   │   ├── tests/test_calculator.py
│   │   └── requirements.txt
│   └── text_analyzer/                    ✅ NLP tool
│       ├── tool.yml
│       ├── scripts/analyzer.py           (tested ✓)
│       └── requirements.txt
│
├── relics/simple/
│   └── kv_store/                         ✅ FastAPI KV store
│       ├── relic.yml
│       ├── app/main.py
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── requirements.txt
│
├── agents/
│   ├── simple/
│   │   └── assistant/                    ✅ Simple agent
│   │       ├── agent.yml                 (with context_feeds)
│   │       ├── system-prompts/assistant.md
│   │       └── tools/time_tool/          (local tool)
│   │           ├── tool.yml
│   │           ├── scripts/time.py       (tested ✓)
│   │           └── requirements.txt
│   │
│   └── complex/
│       └── data_processor/               ✅ Hierarchical agent
│           ├── agent.yml                 (with 5 context_feeds!)
│           ├── system-prompts/
│           │   ├── processor.md
│           │   └── processor_user.md
│           ├── agents/analyzer/          (sub-agent)
│           │   ├── agent.yml
│           │   ├── system-prompts/analyzer.md
│           │   └── tools/stats_tool/     (local to sub-agent)
│           │       ├── tool.yml
│           │       ├── scripts/stats.py  (tested ✓)
│           │       └── requirements.txt
│           ├── relics/results_cache/     (local relic)
│           │   ├── relic.yml
│           │   ├── app/main.py           (TTL cache)
│           │   ├── Dockerfile
│           │   ├── docker-compose.yml
│           │   └── requirements.txt
│           └── workflows/                (local workflow)
│               └── cleanup.workflow.yml
│
├── workflows/simple/
│   └── data_pipeline/                    ✅ ETL workflow
│       ├── workflow.yml                  (proper imports)
│       └── README.md
│
├── monuments/
│   ├── simple/
│   │   └── blog_platform/                ✅ Simple blogging monument
│   │       ├── monument.yml              (3 components)
│   │       ├── docker-compose.yml
│   │       └── README.md
│   ├── complex/
│   │   └── data_analytics_platform/      ✅ Advanced analytics monument
│   │       ├── monument.yml              (10+ components, fractal)
│   │       ├── docker-compose.yml
│   │       └── README.md
│   └── specialized/
│       └── knowledge_base/               ✅ Knowledge management monument
│           ├── monument.yml              (domain-specific)
│           ├── docker-compose.yml
│           └── README.md
│
└── README.md                             📄 This file
```

## Test Coverage

### Tools (2 working)
- ✅ **calculator**: Arithmetic operations (add, subtract, multiply, divide)
- ✅ **text_analyzer**: Word count, sentiment, statistics
- ✅ **stats_tool**: Statistical analysis (local to analyzer sub-agent)
- ✅ **time_tool**: Date/time utilities (local to assistant agent)

### Relics (2 working)
- ✅ **kv_store**: Simple key-value store (FastAPI + SQLite)
- ✅ **results_cache**: TTL cache with auto-cleanup (local to data_processor)

### Agents (2 working)
- ✅ **assistant**: Simple agent with:
  - Local tool: time_tool
  - External tool: calculator
  - Context feeds: current_time, system_info
  
- ✅ **data_processor**: Complex hierarchical agent with:
  - Sub-agent: analyzer (with its own stats_tool)
  - Local relic: results_cache
  - External tools: text_analyzer, calculator
  - External relic: kv_store
  - Local workflow: cleanup
  - 5 context_feeds: cache_stats, processing_queue_size, recent_results, current_timestamp, sub_agent_status

### Workflows (2 working)
- ✅ **text_processing_pipeline**: Uses text_analyzer → stores in kv_store
- ✅ **cleanup**: Cleans up expired cache entries (local to data_processor)

### Monuments (3 complete)
- ✅ **blog_platform**: Simple blogging platform (simple example)
  - Components: content_store relic, writing_assistant agent, publish_pipeline workflow
  - Demonstrates: Minimal monument structure, basic composition
  
- ✅ **data_analytics_platform**: Advanced analytics platform (complex example)
  - Components: 2 relics, hierarchical agents with sub-agents, 3 workflows, 3 tools
  - Demonstrates: Fractal composition, multi-tier storage, scheduled workflows, context feeds
  
- ✅ **knowledge_base**: Knowledge management system (specialized example)
  - Components: 2 relics, 2 agents, 4 workflows, specialized features
  - Demonstrates: Domain-specific architecture, semantic search, quality control, custom health checks

## Testing

### Test Individual Components

```bash
# From repo root:
cd /path/to/Cortex-Prime-MK1

# Test calculator tool
python3 test_against_manifest/tools/simple/calculator/scripts/calculator.py \
  '{"operation": "add", "a": 5, "b": 3}'
# Output: {"success": true, "result": 8, ...}

# Run calculator test suite
python3 test_against_manifest/tools/simple/calculator/tests/test_calculator.py
# Output: ✅ All tests passed!

# Test text analyzer
python3 test_against_manifest/tools/simple/text_analyzer/scripts/analyzer.py \
  '{"operation": "analyze", "text": "This is wonderful!"}'
# Output: {"success": true, "word_count": 3, "sentiment": "positive", ...}

# Test stats tool (local to analyzer sub-agent)
python3 test_against_manifest/agents/complex/data_processor/agents/analyzer/tools/stats_tool/scripts/stats.py \
  '{"operation": "summary", "data": [1, 2, 3, 4, 5]}'
# Output: {"success": true, "summary": {"mean": 3.0, "median": 3.0, ...}}

# Test time tool (local to assistant agent)
python3 test_against_manifest/agents/simple/assistant/tools/time_tool/scripts/time.py \
  '{"operation": "get_datetime"}'
# Output: {"success": true, "datetime": "2025-01-..."}
```

### Test Relic Deployment

```bash
# Deploy KV store (simple relic)
cd test_against_manifest/relics/simple/kv_store
docker-compose up -d
curl http://localhost:8004/health
curl -X POST http://localhost:8004/set \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": {"message": "hello"}}'
curl http://localhost:8004/get/test

# Deploy results_cache (local relic in data_processor agent)
cd test_against_manifest/agents/complex/data_processor/relics/results_cache
docker-compose up -d
curl http://localhost:8005/health
curl http://localhost:8005/stats?include_size=true
curl -X POST http://localhost:8005/store \
  -H "Content-Type: application/json" \
  -d '{"key": "result_1", "value": {"data": "analysis"}, "ttl": 3600}'
curl http://localhost:8005/get/result_1
```

### Validate Manifests

```bash
# Validate all manifests (when validation script exists)
python scripts/validate_manifests.py test_against_manifest/

# Upload to manifest service
curl -X POST -F "file=@test_against_manifest/tools/simple/calculator/tool.yml" \
  http://localhost:8082/manifests/upload
```

## Manifest Standards

All manifests follow v1.0 Sovereign Core Standard:
- Proper `kind`, `version`, `name`, `summary`, `author`, `state` fields
- Complete implementation code (not just YAML)
- Modular directory structure
- Health checks
- Documentation

## Implementation Requirements

Each manifest type includes:

### Tools
- `tool.yml` - Manifest file
- `scripts/` - Implementation code
- `requirements.txt` - Dependencies
- `README.md` - Documentation
- `tests/` - Optional test suite

### Relics
- `relic.yml` - Manifest file
- `app/` - Service implementation
- `Dockerfile` - Container definition
- `docker-compose.yml` - Deployment config
- `requirements.txt` - Dependencies
- `README.md` - Documentation

### Agents
- `agent.yml` - Manifest file
- `system-prompts/` - Persona definitions
- `tools/` - Local tools (optional)
- `agents/` - Sub-agents (optional)
- `relics/` - Local relics (optional)

### Workflows
- `workflow.yml` - Manifest file
- Implementation details TBD

## Example: Complex Agent Import Graph

The `data_processor` agent demonstrates fractal composition:

```
data_processor/
├── imports:
│   ├── agents/analyzer/                     (sub-agent)
│   │   └── imports:
│   │       └── tools/stats_tool/            (local to sub-agent)
│   ├── tools/
│   │   ├── ../../../tools/.../text_analyzer/  (external)
│   │   └── ../../../tools/.../calculator/     (external)
│   ├── relics/
│   │   ├── results_cache/                   (local relic)
│   │   │   └── imports:
│   │   │       └── workflows/cleanup.workflow.yml
│   │   └── ../../../relics/.../kv_store/    (external)
│   └── workflows/
│       └── cleanup.workflow.yml             (local workflow)
└── context_feeds: [cache_stats, queue_size, recent_results, timestamp, sub_agent_status]
```

## Context Feeds Examples

```yaml
# From tool
context_feeds:
  - id: "current_time"
    type: "on_demand"
    source:
      type: "tool"
      name: "time_tool"
      action: "get_datetime"

# From relic
context_feeds:
  - id: "cache_stats"
    type: "periodic"
    interval: 60
    source:
      type: "relic"
      name: "results_cache"
      action: "get_stats"
      params:
        include_size: true

# From sub-agent
context_feeds:
  - id: "sub_agent_status"
    type: "on_demand"
    source:
      type: "agent"
      name: "analyzer"
      action: "get_status"
```

## Monument Testing

### Deploy Simple Monument (Blog Platform)

```bash
cd test_against_manifest/monuments/simple/blog_platform
docker-compose up -d
curl http://localhost:9001/health
```

### Deploy Complex Monument (Analytics Platform)

```bash
cd test_against_manifest/monuments/complex/data_analytics_platform
docker-compose up -d
curl http://localhost:9002/health
curl http://localhost:9002/analytics/stats
```

### Deploy Specialized Monument (Knowledge Base)

```bash
cd test_against_manifest/monuments/specialized/knowledge_base
docker-compose up -d
curl http://localhost:9003/health
curl http://localhost:9003/kb/stats
```

## Next Steps

- [x] Add monument examples (3 complete: simple, complex, specialized)
- [ ] Add container-based tools
- [ ] Add vector store relic
- [ ] Add amulet examples
- [ ] Add validation scripts
- [ ] Add end-to-end integration tests
