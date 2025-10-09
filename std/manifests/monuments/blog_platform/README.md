# Blog Platform Monument

**Simple autonomous blogging platform with AI content assistant**

## Overview

This is a simple monument demonstrating the minimal viable structure:
- Infrastructure: Content storage (KV store)
- Intelligence: AI writing assistant
- Automation: Publishing workflow

## Architecture

```
blog_platform/
├── monument.yml              # Monument manifest
├── docker-compose.yml        # Deployment configuration
└── README.md                 # This file

Imports:
├── Relic: ../../../relics/simple/kv_store/
├── Agent: ../../../agents/simple/assistant/
└── Workflow: ../../../workflows/simple/data_pipeline/
```

## Components

### Infrastructure (Relics)
- **content_store**: Simple KV store for blog posts and metadata

### Intelligence (Agents)
- **writing_assistant**: AI assistant to help write and edit content

### Automation (Workflows)
- **publish_pipeline**: Process and publish blog content

## Deployment

```bash
# From this directory
docker-compose up -d

# Check health
curl http://localhost:9001/health

# Create a post
curl -X POST http://localhost:9001/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "Hello, world!",
    "tags": ["intro", "blog"]
  }'

# Get all posts
curl http://localhost:9001/posts

# Get specific post
curl http://localhost:9001/posts/1
```

## Features

- Markdown support
- AI writing assistance
- Auto-tagging
- Scheduled publishing

## Limits

- Max posts: 1,000
- Max post size: 50KB
- Concurrent users: 10

## Testing

This monument is part of the test suite to validate:
- ✅ Simple monument structure
- ✅ Basic component composition
- ✅ Relative path imports
- ✅ Single-layer architecture

## Resource Usage

**Estimated**: Low
- CPU: 0.5 cores
- RAM: 512MB
- Storage: 1GB
