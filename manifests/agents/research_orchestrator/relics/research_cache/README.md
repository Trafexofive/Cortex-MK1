# Research Cache Relic

**Vector store with TTL and automated cleanup workflows**

## Overview

A caching service local to the research_orchestrator agent that provides key-value storage with time-to-live (TTL) support and automated cleanup workflows.

## Features

- **TTL Support**: Automatic expiration of cached entries
- **Statistics**: Cache hit rates, size, entry counts
- **Search**: Simple key-based search
- **Cleanup Workflow**: Automated expired entry removal
- **Access Tracking**: Track access counts and timestamps

## Endpoints

- `GET /health` - Health check
- `POST /store` - Store item with TTL
- `GET /get/{key}` - Retrieve item (updates access stats)
- `DELETE /delete/{key}` - Delete item
- `POST /cleanup` - Remove expired entries (called by workflow)
- `GET /stats` - Get cache statistics
- `GET /search?query=...&limit=10` - Search cache keys

## Deployment

```bash
cd manifests/agents/research_orchestrator/relics/research_cache
docker-compose up -d
```

Service will be available at `http://localhost:8005`

## Usage

### Store a cache entry
```bash
curl -X POST http://localhost:8005/store \
  -H "Content-Type: application/json" \
  -d '{
    "key": "research:ai:123",
    "value": {"findings": "...", "sources": []},
    "ttl": 3600
  }'
```

### Retrieve entry
```bash
curl http://localhost:8005/get/research:ai:123
```

### Get statistics
```bash
curl http://localhost:8005/stats
```

### Trigger cleanup (normally done by workflow)
```bash
curl -X POST http://localhost:8005/cleanup
```

## Integration

Used by research_orchestrator agent to cache research results.

The cache automatically imports and runs cleanup workflows:
```yaml
import:
  workflows:
    - "./workflows/cache_cleanup.workflow.yml"
```

## Storage

- Backend: SQLite
- Volume: `/data/research_cache.db`
- Persistence: Docker volume `cache_data`

## Configuration

Environment variables:
- `VECTOR_DIMENSION`: 1536 (for future vector support)
- `INDEX_TYPE`: HNSW (for future vector indexing)

## Manifest

- **Path:** `agents/research_orchestrator/relics/research_cache/relic.yml`
- **Version:** 1.0
- **State:** stable
- **Port:** 8005
