# Knowledge Base Monument

**Specialized autonomous knowledge management system with intelligent retrieval**

## Overview

This is a specialized monument demonstrating domain-specific architecture:
- Knowledge management focus
- Semantic search capabilities
- Automated curation workflows
- Quality control systems
- Self-maintaining knowledge graph

## Architecture

```
knowledge_base/
├── monument.yml              # Monument manifest
├── docker-compose.yml        # Deployment with specialized services
└── README.md                 # This file

Imports:
├── Relics:
│   ├── ../../../relics/simple/kv_store/                    (document storage)
│   └── ../../../agents/.../relics/results_cache/           (semantic cache)
├── Agents:
│   ├── ../../../agents/complex/data_processor/             (knowledge curator)
│   └── ../../../agents/simple/assistant/                   (query assistant)
├── Workflows:
│   ├── ../../../workflows/simple/data_pipeline/            (document ingestion)
│   └── ../../../agents/.../workflows/cleanup.workflow.yml  (cache optimization)
└── Tools:
    ├── ../../../tools/simple/text_analyzer/                (content analysis)
    └── ../../../tools/simple/calculator/                   (relevance scoring)
```

## Components

### Infrastructure (Relics)
- **knowledge_store**: Document and metadata storage with schema validation
- **semantic_cache**: Cached query results and embeddings (TTL: 2 hours)
- **embedding_service**: Semantic embeddings for search

### Intelligence (Agents)
- **knowledge_curator**: Organizes and curates content (data_processor agent)
- **query_assistant**: Helps users find and understand knowledge (assistant agent)

### Automation (Workflows)
- **document_ingestion**: Validate, extract metadata, analyze, store (on-demand)
- **knowledge_graph_update**: Update relationships (every 4 hours)
- **cache_optimization**: Optimize cache, remove stale entries (daily 2 AM)
- **content_quality_review**: Review and flag low-quality content (weekly Sunday 10 AM)

### Tools
- **text_analyzer**: Analyze document content and extract insights
- **calculator**: Compute relevance scores and statistics

## Deployment

```bash
# From this directory
docker-compose up -d

# Check health
curl http://localhost:9003/health

# Add a document
curl -X POST http://localhost:9003/kb/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to AI",
    "content": "Artificial Intelligence is...",
    "tags": ["ai", "introduction"],
    "author": "John Doe"
  }'

# Search knowledge base
curl -X POST http://localhost:9003/kb/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "limit": 10
  }'

# Semantic search with AI
curl -X POST http://localhost:9003/kb/query/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "context": true
  }'

# Get document
curl http://localhost:9003/kb/documents/doc-123

# Get related documents
curl http://localhost:9003/kb/documents/doc-123/related

# Get statistics
curl http://localhost:9003/kb/stats
```

## Specialized Features

### Knowledge Management Capabilities

1. **Auto-summarization**: Automatically generate document summaries
2. **Cross-reference detection**: Find related content automatically
3. **Topic modeling**: LDA-based topic extraction
4. **Entity extraction**: Extract persons, organizations, locations, concepts
5. **Version tracking**: Track up to 10 versions per document

### Search Algorithms

- Keyword match
- Semantic similarity
- Hybrid ranking (default)
- Max results: 50

### Quality Control

- Auto-review enabled
- Quality threshold: 0.7
- Flag outdated content (>180 days)
- Weekly quality review workflow

## Features

- Semantic search
- Auto-categorization
- Knowledge graph
- Quality scoring
- Duplicate detection
- Auto-tagging
- Relationship discovery
- Citation tracking

## Context Feeds

Domain-specific context awareness:
- **kb_statistics**: Document count, quality metrics, etc. (every 5 min)
- **popular_queries**: Top 10 queries from cache (every 10 min)
- **curator_status**: Knowledge curator agent status (on-demand)

## Limits

- Max documents: 100,000
- Max document size: 10MB
- Max query length: 500 chars
- Concurrent queries: 50

## Custom Metrics

- total_documents
- query_latency_p95
- search_accuracy
- cache_hit_rate
- quality_score_avg

## Health Checks

- **Liveness**: /health/live (every 30s)
- **Readiness**: /health/ready (every 10s)
- **Custom**: /health/graph (knowledge graph health, every 5 min)

## Testing

This monument is part of the test suite to validate:
- ✅ Domain-specific monument architecture
- ✅ Specialized capabilities configuration
- ✅ Custom metrics and health checks
- ✅ Advanced workflow automation
- ✅ Multi-agent coordination
- ✅ Background workers
- ✅ Specialized services integration

## Resource Usage

**Estimated**: Medium
- CPU: 1.5 cores (limit), 0.5 cores (reserved)
- RAM: 1.5GB (limit), 512MB (reserved)
- Storage: 20GB (documents + index)
- Network: Private bridge network

## Advanced Patterns Demonstrated

1. **Domain Specialization**: Knowledge management focused architecture
2. **Multi-service Coordination**: API + workers + cache + embedding service
3. **Quality Systems**: Automated quality review and content curation
4. **Semantic Intelligence**: Embedding-based search with AI assistance
5. **Self-maintenance**: Automated graph updates and cache optimization
6. **Custom Health Checks**: Domain-specific health monitoring

## Use Cases

- Corporate knowledge base
- Documentation system
- Research repository
- FAQ system
- Content library
- Educational resources
