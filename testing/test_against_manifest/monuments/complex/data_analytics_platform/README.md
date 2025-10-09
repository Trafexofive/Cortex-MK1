# Data Analytics Platform Monument

**Advanced autonomous data analytics platform with hierarchical AI processing**

## Overview

This is a complex monument demonstrating advanced patterns:
- Multi-tier storage infrastructure
- Hierarchical agent architecture with sub-agents
- Multiple automated workflows
- Fractal composition (sub-agents with local tools)

## Architecture

```
data_analytics_platform/
├── monument.yml              # Monument manifest
├── docker-compose.yml        # Deployment with scaling
└── README.md                 # This file

Imports:
├── Relics:
│   ├── ../../../relics/simple/kv_store/                    (persistent storage)
│   └── ../../../agents/.../relics/results_cache/           (processing cache)
├── Agents:
│   └── ../../../agents/complex/data_processor/             (orchestrator)
│       └── agents/analyzer/                                (sub-agent)
│           └── tools/stats_tool/                           (local tool)
├── Workflows:
│   ├── ../../../workflows/simple/data_pipeline/            (ingestion)
│   └── ../../../agents/.../workflows/cleanup.workflow.yml  (maintenance)
└── Tools:
    ├── ../../../tools/simple/text_analyzer/
    └── ../../../tools/simple/calculator/
```

## Components

### Infrastructure (Relics)
- **persistent_store**: Long-term data storage (KV store)
- **processing_cache**: High-speed cache with TTL for processing results

### Intelligence (Agents)
- **data_orchestrator**: Main orchestrator (data_processor agent)
  - **analyzer**: Sub-agent for statistical analysis
    - **stats_tool**: Local tool for statistics (demonstrates fractal composition)

### Automation (Workflows)
- **data_ingestion_pipeline**: Ingest and process raw data (on-demand)
- **cache_maintenance**: Clean expired cache entries (every 6 hours)
- **analytics_report**: Generate weekly reports (Mondays at 9 AM)

### Tools
- **text_analyzer**: Analyze text data
- **calculator**: Mathematical computations
- **stats_tool**: Statistical analysis (local to analyzer sub-agent)

## Deployment

```bash
# From this directory
docker-compose up -d

# Check health
curl http://localhost:9002/health

# Submit data for analysis
curl -X POST http://localhost:9002/analytics/submit \
  -H "Content-Type: application/json" \
  -d '{
    "data": [1, 2, 3, 4, 5, 10, 15, 20],
    "analysis_type": "full"
  }'

# Get results
curl http://localhost:9002/analytics/results/job-123

# Get platform statistics
curl http://localhost:9002/analytics/stats

# Trigger workflow manually
curl -X POST http://localhost:9002/workflows/cache_maintenance/trigger

# View metrics
curl http://localhost:9002/metrics
```

## Features

- Real-time processing
- Batch processing
- Automatic scaling (1-3 instances)
- Result caching
- Hierarchical agents
- Sub-agent delegation
- Workflow automation
- Health monitoring

## Context Feeds

Monument-level context awareness:
- **platform_metrics**: Overall system metrics (every 30s)
- **cache_health**: Cache statistics from processing_cache (every 60s)
- **queue_status**: Job queue status from data_orchestrator (on-demand)

## Limits

- Max concurrent jobs: 100
- Max job size: 100MB
- Max cache entries: 10,000
- Job timeout: 1 hour

## Performance Targets

- Latency: < 200ms
- Throughput: 50 jobs/second

## Scaling

Horizontal scaling configured for data_orchestrator:
- Min instances: 1
- Max instances: 3
- Trigger: CPU > 70%

## Monitoring

Available at:
- Metrics: http://localhost:9002/metrics
- Health (live): http://localhost:9002/health/live
- Health (ready): http://localhost:9002/health/ready
- Prometheus: http://localhost:9090

## Testing

This monument is part of the test suite to validate:
- ✅ Complex monument structure
- ✅ Hierarchical agent composition
- ✅ Multiple storage backends
- ✅ Local and external imports
- ✅ Scheduled workflows
- ✅ Context feeds
- ✅ Fractal composition pattern

## Resource Usage

**Estimated**: Medium
- CPU: 2 cores (limit), 0.5 cores (reserved)
- RAM: 2GB (limit), 512MB (reserved)
- Storage: 10GB
- Network: Private bridge network

## Advanced Patterns Demonstrated

1. **Fractal Composition**: data_processor → analyzer → stats_tool
2. **Mixed Imports**: External relics + local relics + local workflows
3. **Multi-tier Storage**: Persistent store + cache layer
4. **Hierarchical Intelligence**: Orchestrator → worker sub-agents
5. **Automated Maintenance**: Scheduled cleanup workflows
6. **Context Awareness**: Monument-level context feeds from components
