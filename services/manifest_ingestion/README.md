# 🚀 Cortex-Prime Manifest Ingestion Service

**"Sovereign manifests, intelligently parsed and validated."**

## Overview

The **Manifest Ingestion Service** is a FastAPI + Pydantic microservice that provides intelligent parsing, validation, and registry management for Cortex-Prime's custom markdown manifests. It serves as the central authority for all manifest lifecycle operations in the ecosystem.

## Philosophy

- **Sovereignty**: Each manifest defines a complete, autonomous entity
- **Declarative**: Manifests are the single source of truth for system configuration
- **Strongly Typed**: All manifests are validated using comprehensive Pydantic models
- **Dependency-Aware**: Automatic resolution and validation of inter-manifest dependencies
- **Extensible**: Plugin-based architecture supporting multiple manifest formats

## Features

### 🔍 Intelligent Parsing
- **Multi-format Support**: YAML, Markdown with YAML frontmatter, mixed formats
- **Auto-detection**: Automatically determines parsing strategy based on content
- **Path Resolution**: Resolves relative paths to absolute paths during parsing
- **Error Handling**: Comprehensive error reporting with context

### 📋 Manifest Types
- **Agents**: Autonomous cognitive entities with personas and capabilities
- **Tools**: Stateless functions and utilities
- **Relics**: Stateful, persistent services
- **Workflows**: Multi-step declarative pipelines

### 🔗 Dependency Management
- **Dependency Resolution**: Tracks and resolves inter-manifest dependencies
- **Validation**: Ensures all dependencies are satisfied before registration
- **Dependency Graph**: Builds complete dependency graphs for visualization
- **Circular Detection**: Prevents circular dependency issues

### 🗄️ Registry Management
- **In-Memory Registry**: High-performance in-memory manifest storage
- **Filesystem Sync**: Bidirectional synchronization with filesystem manifests
- **Export/Import**: JSON export for backup and migration
- **Statistics**: Real-time registry statistics and health monitoring

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /registry/status` - Registry statistics and status

### Manifest Ingestion
- `POST /manifests/upload` - Upload and register a manifest file
- `POST /manifests/parse` - Parse manifest content for validation

### Registry Queries
- `GET /registry/agents` - List all agent manifests
- `GET /registry/tools` - List all tool manifests  
- `GET /registry/relics` - List all relic manifests
- `GET /registry/workflows` - List all workflow manifests
- `GET /registry/manifest/{type}/{name}` - Get specific manifest

### Dependency Management
- `GET /registry/dependencies/{type}/{name}` - Get manifest dependencies
- `GET /registry/validate-dependencies/{type}/{name}` - Validate dependencies

### Filesystem Operations
- `POST /registry/sync` - Sync registry with filesystem
- `POST /registry/export` - Export complete registry

## Configuration

### Environment Variables

```bash
# Server Configuration
HOST=0.0.0.0                    # Server host
PORT=8082                       # Server port  
LOG_LEVEL=info                  # Logging level

# Manifest Configuration
MANIFESTS_ROOT=/app/manifests   # Root directory for manifests
AUTO_SYNC_FILESYSTEM=true       # Auto-sync with filesystem on startup

# Registry Configuration  
REGISTRY_CACHE_TTL=3600         # Registry cache TTL in seconds

# CORS Configuration
CORS_ORIGINS=*                  # Allowed CORS origins
```

## Usage Examples

### Upload a Manifest
```bash
curl -X POST "http://localhost:8082/manifests/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@agent.yml"
```

### Parse Manifest Content
```bash
curl -X POST "http://localhost:8082/manifests/parse" \
     -H "Content-Type: application/json" \
     -d '{"content": "kind: Agent\nname: test\nversion: 1.0\nsummary: Test agent"}'
```

### Get Registry Status
```bash
curl http://localhost:8082/registry/status
```

### List All Agents
```bash
curl http://localhost:8082/registry/agents
```

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py

# Run tests
pytest tests/
```

### Docker Development
```bash
# Build image
docker build -t cortex-manifest-ingestion .

# Run container
docker run -p 8082:8082 \
           -v $(pwd)/../../manifests:/app/manifests \
           cortex-manifest-ingestion
```

## Integration with Cortex-Prime

The Manifest Ingestion Service integrates seamlessly with the Cortex-Prime ecosystem:

1. **Chimera Core**: The C++ arbiter queries this service for manifest data
2. **API Gateway**: Routes manifest management requests through this service  
3. **LLM Gateway**: Uses manifest metadata for cognitive engine configuration
4. **Agent Factory**: Instantiates agents based on validated manifests

## Manifest Format

### Agent Manifest Example
```yaml
kind: Agent
version: "1.0"
name: "example_agent"
summary: "Example agent for demonstration"
author: "PRAETORIAN_CHIMERA"
state: "stable"

persona:
  agent: "./prompts/example.md"
  
agency_level: "default"
grade: "common" 
iteration_cap: 10

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"
  parameters:
    temperature: 0.7
    max_tokens: 4096

import:
  tools:
    - "filesystem"
    - "./tools/web_search/tool.yml"
  relics:
    - "./relics/memory_store/relic.yml"

context_feeds:
  - id: "current_time"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"

environment:
  variables:
    EXAMPLE_VAR: "example_value"
```

## Testing

The service includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_parser.py -v
```

## Architecture

```
manifest_ingestion/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── models/
│   └── manifest_models.py  # Pydantic models for all manifest types
├── parsers/
│   └── manifest_parser.py  # Intelligent manifest parsing logic
├── registry/
│   └── manifest_registry.py # Registry service and dependency management
├── tests/
│   ├── test_parser.py      # Parser tests
│   └── test_registry.py    # Registry tests
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
└── README.md              # This file
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure all tests pass before submitting

## License

Part of the Cortex-Prime MK1 ecosystem.
**"The distance between thought and action, minimized."**