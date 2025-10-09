# Test Manifests - Quick Start

## ✅ Complete Test Suite Created

**19 YAML manifests** | **7 Python implementations** | **46 total files**

### Tools (4 working)
1. **calculator** - Arithmetic operations with full tests
2. **text_analyzer** - Text analysis with sentiment detection
3. **stats_tool** - Statistical analysis (local to analyzer sub-agent)
4. **time_tool** - Date/time utilities (local to assistant agent)

### Relics (2 with Docker deployment)
1. **kv_store** - FastAPI + SQLite KV store (port 8004)
2. **results_cache** - TTL cache with auto-cleanup (port 8005, local to data_processor)

### Agents (2 complete hierarchies)
1. **assistant** - Simple agent
   - Local tool: time_tool
   - External tool: calculator (relative import)
   - Context feeds: current_time, system_info

2. **data_processor** - Complex hierarchical agent  
   - Sub-agent: analyzer
   - Local relic: results_cache
   - Local workflow: cleanup
   - External tools: text_analyzer, calculator (relative imports)
   - External relic: kv_store (relative import)
   - 5 context_feeds!

### Workflows (2 complete)
1. **text_processing_pipeline** - ETL workflow
2. **cleanup** - Cache maintenance (local to data_processor)

### Monuments (3 complete)
1. **blog_platform** - Simple blogging platform (simple)
2. **data_analytics_platform** - Advanced analytics (complex, fractal)
3. **knowledge_base** - Knowledge management system (specialized, domain-specific)

## Quick Tests (All Verified ✅)

```bash
# From repo root: cd /path/to/Cortex-Prime-MK1

# Test calculator tool
python3 test_against_manifest/tools/simple/calculator/scripts/calculator.py \
  '{"operation": "multiply", "a": 7, "b": 6}'
# Output: {"success": true, "result": 42, ...}

# Run calculator test suite
python3 test_against_manifest/tools/simple/calculator/tests/test_calculator.py
# Output: ✅ All tests passed!

# Test text analyzer
python3 test_against_manifest/tools/simple/text_analyzer/scripts/analyzer.py \
  '{"operation": "analyze", "text": "This is wonderful!"}'
# Output: {"success": true, "word_count": 3, "sentiment": "positive", ...}

# Test stats tool (local to analyzer sub-agent)
python3 test_against_manifest/agents/complex/data_processor/agents/analyzer/tools/stats_tool/scripts/stats.py \
  '{"operation": "summary", "data": [1, 2, 3, 4, 5, 10, 15, 20]}'
# Output: {"success": true, "summary": {"mean": 7.5, "median": 4.5, ...}}

# Test time tool (local to assistant agent)
python3 test_against_manifest/agents/simple/assistant/tools/time_tool/scripts/time.py \
  '{"operation": "get_datetime"}'
# Output: {"success": true, "datetime": "2025-01-..."}
```

## Deploy Relics

```bash
# KV Store (simple relic)
cd test_against_manifest/relics/simple/kv_store
docker-compose up -d
curl http://localhost:8004/health
curl -X POST http://localhost:8004/set \
  -H "Content-Type: application/json" \
  -d '{"key": "greeting", "value": {"message": "hello"}}'
curl http://localhost:8004/get/greeting

# Results Cache (local to data_processor agent)
cd test_against_manifest/agents/complex/data_processor/relics/results_cache
docker-compose up -d
curl http://localhost:8005/health
curl http://localhost:8005/stats?include_size=true
curl -X POST http://localhost:8005/store \
  -H "Content-Type: application/json" \
  -d '{"key": "result_1", "value": {"analysis": "complete"}, "ttl": 3600}'
curl http://localhost:8005/get/result_1
```

## Deploy Monuments

```bash
# Blog Platform (simple monument)
cd test_against_manifest/monuments/simple/blog_platform
docker-compose up -d
curl http://localhost:9001/health

# Data Analytics Platform (complex monument with fractal composition)
cd test_against_manifest/monuments/complex/data_analytics_platform
docker-compose up -d
curl http://localhost:9002/health
curl http://localhost:9002/analytics/stats

# Knowledge Base (specialized monument with domain-specific features)
cd test_against_manifest/monuments/specialized/knowledge_base
docker-compose up -d
curl http://localhost:9003/health
curl http://localhost:9003/kb/stats
```

## Manifest Structure

Each manifest follows the modular structure:

```
component_name/
├── {tool|relic|agent|workflow}.yml    # Manifest file
├── scripts/ or app/                    # Implementation code
├── requirements.txt                    # Python dependencies
├── README.md                           # Documentation
├── tests/                              # Tests (optional)
└── {Dockerfile, docker-compose.yml}    # For relics
```

## Key Improvements from Requirements

### ✅ Proper Relative Path Imports
**NO MAGIC GLOBALS!** All imports are explicit:
```yaml
# Old (wrong): assumes global registry
import:
  tools: ["calculator"]

# New (correct): explicit relative path
import:
  tools: ["../../../tools/simple/calculator/tool.yml"]
```

### ✅ Context Feeds Implemented
Agents now have dynamic data injection:
```yaml
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
```

### ✅ Fractal Composition Demonstrated
- data_processor has sub-agent (analyzer)
- analyzer has local tool (stats_tool)
- data_processor has local relic (results_cache)
- results_cache has local workflow (cleanup)
- All imports use relative paths that work from anywhere!

## Import Graph Example

```
data_processor/agent.yml imports:
  ├── ./agents/analyzer/agent.yml
  │   └── ./tools/stats_tool/tool.yml
  ├── ./relics/results_cache/relic.yml
  │   └── ../../workflows/cleanup.workflow.yml
  ├── ../../../tools/simple/text_analyzer/tool.yml
  ├── ../../../tools/simple/calculator/tool.yml
  └── ../../../relics/simple/kv_store/relic.yml
```

This structure works whether you upload from:
- `/test_against_manifest/`
- A client machine
- Any subdirectory
- Different repository clone
