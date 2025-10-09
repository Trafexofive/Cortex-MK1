# Container Orchestrator

**"The Docker Wrangler" - Container lifecycle management for Cortex-Prime**

Port: 8086

## Overview

The Container Orchestrator manages all Docker container operations in Cortex-Prime:
- **Tool Execution**: Ephemeral containers for tool scripts
- **Relic Management**: Session-scoped stateful containers
- **Network Isolation**: Private networks per session
- **Resource Limits**: Memory, CPU, timeout enforcement
- **Health Checks**: Monitor relic health
- **Auto-Cleanup**: Container and network cleanup

## Features

- **Docker SDK Integration**: Full Docker API access
- **Ephemeral Tool Containers**: Run and cleanup immediately
- **Session-Scoped Relics**: Containers that live with agent sessions
- **Private Networks**: Isolated networks per session for relics
- **Resource Monitoring**: CPU, memory, network, disk stats
- **Health Checks**: Wait for relic readiness
- **Automatic Cleanup**: Remove containers and networks on session end

## Architecture

```
container_orchestrator/
├── main.py                     # FastAPI application
├── models/
│   └── container_models.py     # Pydantic models
├── managers/
│   ├── docker_manager.py       # Container lifecycle
│   └── network_manager.py      # Network management
├── api/
│   ├── tools.py                # Tool execution endpoints
│   ├── relics.py               # Relic management endpoints
│   ├── stats.py                # Stats endpoints
│   └── cleanup.py              # Cleanup endpoints
├── Dockerfile
├── requirements.txt
├── test_service.py
└── README.md
```

## API Endpoints

### Tool Execution
```bash
POST   /containers/tool/execute          # Execute tool in container
GET    /containers/tool/{id}             # Get execution result
GET    /containers/tool/{id}/logs        # Get execution logs
POST   /containers/tool/{id}/cancel      # Cancel execution
```

### Relic Management
```bash
POST   /containers/relic/start           # Start relic container
GET    /containers/relic/{id}            # Get relic info
GET    /containers/relic?session_id=X    # List relics (filtered)
POST   /containers/relic/{id}/stop       # Stop relic
DELETE /containers/relic/{id}            # Delete relic
```

### Stats
```bash
GET    /containers/stats                 # All container stats
GET    /containers/stats/{id}            # Specific container stats
```

### Cleanup
```bash
POST   /containers/cleanup/session       # Cleanup session containers
POST   /containers/cleanup/all-networks  # Cleanup all networks
```

## Usage Examples

### Execute a Tool

```bash
curl -X POST http://localhost:8086/containers/tool/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "pdf_extractor",
    "session_id": "session_abc123",
    "parameters": {"file": "document.pdf"},
    "image": "cortex/tool-pdf-extractor:latest",
    "resource_limits": {
      "memory_mb": 512,
      "cpu_limit": 1.0,
      "timeout_seconds": 300
    },
    "cleanup": true
  }'
```

### Start a Relic

```bash
curl -X POST http://localhost:8086/containers/relic/start \
  -H "Content-Type: application/json" \
  -d '{
    "relic_name": "research_cache",
    "session_id": "session_abc123",
    "image": "cortex/relic-research-cache:latest",
    "resource_limits": {
      "memory_mb": 1024,
      "cpu_limit": 2.0,
      "timeout_seconds": 600
    },
    "create_private_network": true,
    "health_check_endpoint": "/health",
    "health_check_timeout_seconds": 30
  }'
```

Response:
```json
{
  "relic_id": "relic_a1b2c3d4e5f6",
  "relic_name": "research_cache",
  "session_id": "session_abc123",
  "status": "running",
  "container_id": "f8e7d6c5b4a3",
  "container_name": "relic_research_cache_session_abc123_a1b2c3d4",
  "network_id": "net_abc123",
  "internal_url": "http://relic_research_cache_session_abc123_a1b2c3d4:8000",
  "healthy": true
}
```

### Get Container Stats

```bash
curl http://localhost:8086/containers/stats
```

### Cleanup Session

```bash
curl -X POST http://localhost:8086/containers/cleanup/session \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_abc123",
    "force": true
  }'
```

## Docker Requirements

The service requires access to the Docker daemon. When running in a container, mount the Docker socket:

```bash
docker run -p 8086:8086 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cortex/container-orchestrator:latest
```

## How It Works

### Tool Execution Flow

1. Client sends tool execution request
2. Service gets/builds Docker image
3. Creates container with resource limits
4. Runs tool script with parameters as env vars
5. Waits for completion (with timeout)
6. Collects stdout/stderr and exit code
7. Parses result (JSON output expected)
8. Records resource usage
9. Removes container (if cleanup=true)

### Relic Lifecycle

1. Client requests relic start
2. Service creates private network for session (if requested)
3. Gets/builds relic image
4. Starts container in private network
5. Waits for health check endpoint
6. Returns internal URL (accessible only from session network)
7. Relic runs until session ends
8. On session cleanup: stop container, remove network

### Private Networks

Each session can have a private Docker network:
- Created on first relic start for session
- All relics for session join this network
- Relics can communicate via container names
- Isolated from other sessions
- Removed on session cleanup

## Resource Limits

All containers enforce:
- **Memory**: Default 512MB (tools), 1GB (relics)
- **CPU**: Default 1.0 cores
- **Timeout**: Default 5 minutes (tools), 10 minutes (relics)
- **Network**: Isolated per session

## Environment Variables

- `HOST`: Host to bind to (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 8086)
- `LOG_LEVEL`: Logging level (default: INFO)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Docker is running
docker info

# Run service
python main.py

# Test
python test_service.py
```

## Docker

```bash
# Build
docker build -t cortex/container-orchestrator .

# Run (requires Docker socket)
docker run -p 8086:8086 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cortex/container-orchestrator
```

## Dependencies

- fastapi==0.115.5
- uvicorn==0.32.1
- pydantic==2.10.3
- loguru==0.7.3
- docker==7.1.0
- httpx==0.28.1

## Security Considerations

- **Docker Socket**: Service needs access to Docker daemon (security risk)
- **Resource Limits**: Always enforce to prevent resource exhaustion
- **Network Isolation**: Use private networks for relics
- **Image Trust**: Only use trusted Docker images
- **Cleanup**: Always cleanup containers to prevent accumulation

## Future Enhancements

- [ ] Volume management for persistent data
- [ ] Image caching for faster startup
- [ ] Container health monitoring
- [ ] Resource usage alerts
- [ ] Multi-host orchestration
- [ ] Kubernetes support

## License

Part of Cortex-Prime MK1 ecosystem.
