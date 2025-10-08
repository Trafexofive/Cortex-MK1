# Infrastructure Guide

## Directory Structure

```
infra/
├── docker-compose.yml       # Full stack (all services)
├── docker-compose.core.yml  # Minimal stack (core services only)
├── env/
│   ├── .env                 # Active environment config
│   ├── .env.template        # Template for new environments
│   ├── .env.prod            # Production config (optional)
│   └── .env.testing         # Testing config (optional)
├── nginx/                   # NGINX configuration
└── settings.yml             # Global settings
```

## Stack Variants

### Full Stack (`docker-compose.yml`)
Complete system with all services:
- Neo4j (graph database)
- Redis (cache)
- LLM Gateway
- Chat Test Service
- Manifest Ingestion
- Runtime Executor
- API Gateway
- Web Client

**Use when**: Running the complete system, production deployments

### Core Stack (`docker-compose.core.yml`)
Minimal services for development:
- Redis (lightweight cache)
- LLM Gateway (AI provider abstraction)
- Chat Test Service (development interface)
- Web Client (optional UI)

**Use when**: Developing, testing simple agent loops, limited resources

## Makefile Commands

### Basic Operations

```bash
# Start full stack
make up

# Start core stack
make up STACK=core

# Stop services
make down
make down STACK=core

# Restart
make restart
make restart STACK=core

# Check status
make status
make status STACK=core

# View logs
make logs
make logs service=llm_gateway
make logs STACK=core
```

### Building

```bash
# Build all services
make build

# Build specific service
make build service=llm_gateway

# Rebuild from scratch
make rebuild
make rebuild service=chat_test
```

### Environment Management

```bash
# Check if .env exists
make env-check

# Create .env from template
make env-create
```

### Monitoring

```bash
# Check service health
make health

# SSH into container
make ssh service=llm_gateway

# Execute command in container
make exec svc=llm_gateway cmd="ls -la"
```

## Environment Variables

### Required Variables

Located in `infra/env/.env`:

```env
# Project
PROJECT_NAME=graphrag-agent-mk1

# LLM Providers
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here

# Neo4j (full stack only)
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Ports
LLM_GATEWAY_HOST_PORT=8081
CHAT_TEST_HOST_PORT=8888
REDIS_HOST_PORT=6380
```

### Environment File Precedence

1. `infra/env/.env` - Active configuration (used by default)
2. `infra/env/.env.testing` - Testing environment
3. `infra/env/.env.prod` - Production environment

To use a different env file:
```bash
# Copy desired config to .env
cp infra/env/.env.prod infra/env/.env
```

## Service Ports

### Core Stack
- **8081**: LLM Gateway API
- **8888**: Chat Test Interface
- **8889**: Web Client (optional)
- **6380**: Redis

### Full Stack (additional)
- **7474**: Neo4j Browser
- **7687**: Neo4j Bolt
- **8082**: Manifest Ingestion
- **8083**: Runtime Executor
- **8084**: API Gateway

## Docker Compose Details

### Network Configuration

Both stacks create isolated networks:
- Full stack: `graphrag-agent-mk1_network`
- Core stack: `graphrag-agent-mk1_core_network`

### Volume Management

Persistent volumes for data:
- `redis_data`: Redis persistence
- `neo4j_data`: Neo4j database (full stack only)

### Health Checks

All services have health checks:
- LLM Gateway: `http://localhost:8080/health`
- Chat Test: `http://localhost:8888/health`
- Redis: `redis-cli ping`
- Neo4j: Cypher query check

## Troubleshooting

### Services Won't Start

1. Check env file exists:
   ```bash
   make env-check
   ```

2. Verify configuration:
   ```bash
   docker compose -f infra/docker-compose.core.yml config
   ```

3. Check logs:
   ```bash
   make logs STACK=core
   ```

### Port Conflicts

If ports are in use, update in `infra/env/.env`:
```env
LLM_GATEWAY_HOST_PORT=9081
CHAT_TEST_HOST_PORT=9888
```

### Environment Variables Not Loading

The Makefile automatically passes `--env-file infra/env/.env` to docker-compose.
Variables are loaded in this order:
1. Makefile defaults
2. `infra/env/.env`
3. Docker Compose defaults

### Clean Start

```bash
# Stop everything
make down

# Remove all containers and volumes
make fclean

# Start fresh
make up STACK=core
```

## Development Workflow

### 1. Initial Setup

```bash
# Create environment file
make env-create

# Edit with your API keys
nano infra/env/.env

# Start core stack for development
make up STACK=core
```

### 2. Development Iteration

```bash
# Make code changes
# ...

# Rebuild and restart service
make rebuild service=chat_test

# Check logs
make logs service=chat_test

# Test
curl http://localhost:8888/health
```

### 3. Testing Full Stack

```bash
# Stop core stack
make down STACK=core

# Start full stack
make up

# Run integration tests
make test-integration
```

## Best Practices

1. **Use Core Stack for Development**
   - Faster startup
   - Lower resource usage
   - Easier debugging

2. **Keep Environment Files Secure**
   - Never commit `infra/env/.env` to git
   - Use `.env.template` for documentation
   - Rotate API keys regularly

3. **Monitor Service Health**
   - Check `make status` regularly
   - Set up healthcheck monitoring
   - Review logs for errors

4. **Clean Up Regularly**
   - Remove unused volumes: `make fclean`
   - Prune Docker system: `make prune`
   - Keep only necessary containers running

## Quick Reference

| Task | Command |
|------|---------|
| Start dev environment | `make up STACK=core` |
| Start full system | `make up` |
| Stop services | `make down` |
| View logs | `make logs` |
| Check status | `make status` |
| Rebuild service | `make rebuild service=<name>` |
| Shell access | `make ssh service=<name>` |
| Clean everything | `make fclean` |

## Additional Resources

- [Repository Structure](./REPOSITORY_STRUCTURE.md)
- [LLM Gateway Integration](./LLM_GATEWAY_INTEGRATION.md)
- [Reorganization Summary](./REORGANIZATION_SUMMARY.md)
