# 🏛️ Cortex-Prime MK1

> **"The distance between thought and action, minimized."**

A sovereign AI ecosystem implementing the **Himothy Covenant** - a declarative, modular architecture for autonomous AI agents with hot-reloadable manifests, context-aware variables, and containerized execution.

[![Tests](https://img.shields.io/badge/tests-33%2F33%20passing-brightgreen)]()
[![Phase](https://img.shields.io/badge/Phase%200-33%25%20complete-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#%EF%B8%8F-architecture)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 🎯 Overview

Cortex-Prime MK1 is a **sovereign AI orchestration platform** designed for:

- **Declarative Reality**: Define agents, tools, and workflows via YAML manifests
- **Hot-Reload Everything**: Modify manifests and see changes instantly (no restarts)
- **Dynamic Intelligence**: Context variables resolve runtime state (`$TIMESTAMP`, `$AGENT_NAME`, etc.)
- **Modular Design**: Loosely coupled microservices with clean interfaces
- **FAAFO Engineering**: Built for rapid iteration and experimentation

This is the **Minimum Viable Pantheon** - a foundation for building emergent, autonomous AI systems.

---

## ✨ Key Features

### 🔥 Manifest Ingestion Pipeline
- **Multi-format parsing**: YAML and Markdown with frontmatter
- **Schema validation**: Strong typing via Pydantic models
- **Hot-reload**: Filesystem watcher auto-reloads manifests on change
- **Dependency tracking**: Automatic validation of inter-manifest dependencies
- **RESTful API**: FastAPI with OpenAPI documentation

### 🔧 Context Variable System
- **Dynamic resolution**: `$(VARIABLE)` and `${VARIABLE}` syntax
- **22 built-in variables**: Timestamps, agent state, session info, environment
- **Custom resolvers**: Extensible plugin system
- **Scoped contexts**: Global, session, agent, and task levels
- **Recursive resolution**: Works with nested dicts and lists

### ⚙️ Developer Experience
- **Comprehensive Makefile**: 20+ commands for common tasks
- **Settings.yml**: Centralized configuration with environment overrides
- **Health checks**: Monitor service status via API
- **Testing**: 33 tests with 100% pass rate
- **Documentation**: Extensive docs and examples

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cortex-Prime MK1                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  Manifest        │         │  Runtime         │        │
│  │  Ingestion       │◄────────┤  Executor        │        │
│  │  Service         │         │  Service         │        │
│  │  (FastAPI)       │         │  (Sandboxed)     │        │
│  └────────┬─────────┘         └──────────────────┘        │
│           │                                                │
│           │ Manifests (YAML)                              │
│           ▼                                                │
│  ┌──────────────────────────────────────────────┐        │
│  │  Registry                                     │        │
│  │  - Agents  - Tools  - Relics  - Workflows   │        │
│  └──────────────────────────────────────────────┘        │
│                                                             │
│  ┌──────────────────────────────────────────────┐        │
│  │  Supporting Services                         │        │
│  │  - Neo4j (Graph DB)  - Redis (Cache)        │        │
│  └──────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| **Manifest Ingestion** | Parse, validate, and manage manifests | 8082 | ✅ Production |
| **Runtime Executor** | Sandboxed tool execution | 8083 | 🚧 In Progress |
| **Neo4j** | Knowledge graph storage | 7474/7687 | ⚙️ Configured |
| **Redis** | Caching and state | 6379 | ⚙️ Configured |

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **Make** (build automation)
- **jq** (JSON processing, optional but recommended)
- **curl** (API testing)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Trafexofive/Cortex-MK1.git
cd Cortex-MK1

# 2. Create environment configuration
cp .env.template .env
# Edit .env and add your API keys

# 3. Build and start services
make setup

# 4. Verify services are running
make health
```

### First Steps

```bash
# Check service health
curl http://localhost:8082/health

# View registry status
curl http://localhost:8082/registry/status

# Upload a manifest
curl -X POST -F "file=@manifests/agents/journaler/agent.yml" \
  http://localhost:8082/manifests/upload

# Force sync manifests from filesystem
make sync

# View logs
make logs-manifest
```

---

## 💻 Usage

### Creating an Agent Manifest

Create `my_agent.yml`:

```yaml
kind: Agent
version: "1.0"
name: "my_custom_agent"
summary: "Custom agent created at $TIMESTAMP"
author: "YOUR_NAME"
state: "unstable"

persona:
  agent: "./prompts/agent.md"

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

environment:
  variables:
    WORKSPACE: "$HOME/workspace/$AGENT_NAME"
    LOG_FILE: "/logs/$SESSION_ID.log"
```

### Using Context Variables

Manifests support dynamic variables that resolve at runtime:

**Core Variables:**
- `$TIMESTAMP` - Current UTC timestamp (ISO 8601)
- `$DATE`, `$TIME` - Date/time components
- `$AGENT_ID`, `$AGENT_NAME` - Agent identity
- `$SESSION_ID`, `$USER_ID` - Session context
- `$HOME`, `$USER`, `$PWD` - Environment
- `$ITERATION_COUNT`, `$CONFIDENCE` - Execution state

**Example:**
```yaml
environment:
  variables:
    WORKSPACE: "$HOME/workspace/$AGENT_NAME"
    # Resolves to: /home/cortex/workspace/my_custom_agent
```

### API Endpoints

**Manifest Ingestion Service** (`http://localhost:8082`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/registry/status` | GET | Registry statistics |
| `/manifests/upload` | POST | Upload manifest file |
| `/registry/agents` | GET | List all agents |
| `/registry/tools` | GET | List all tools |
| `/registry/sync` | POST | Force filesystem sync |
| `/docs` | GET | Interactive API documentation |

---

## 🛠️ Development

### Makefile Commands

```bash
# === Quick Start ===
make setup              # Build and start entire stack
make up                 # Start all services
make down               # Stop all services
make restart            # Restart services

# === Monitoring ===
make status             # Show service status
make logs               # Follow all logs
make logs-manifest      # Follow manifest service logs
make logs-runtime       # Follow runtime executor logs
make health             # Check all service health

# === Testing ===
make test               # Run all tests
make test-manifest      # Test manifest service
make test-integration   # Run integration tests

# === Manifest Operations ===
make sync               # Force manifest sync
make validate           # Validate all manifests

# === Cleaning ===
make clean              # Remove containers
make fclean             # Remove containers + volumes
make prune              # Full system clean

# === Development ===
make ssh service=<name> # Shell into service
make exec svc=<name> cmd="<cmd>" # Execute command
make build              # Build images (cached)
make rebuild            # Build images (no cache)
```

### Running Tests

```bash
# All tests
make test

# Specific test suite
make test-manifest

# Inside container
docker run --rm -v $(pwd)/services/manifest_ingestion:/app -w /app \
  cortex-prime-mk1-manifest_ingestion \
  python -m pytest tests/ -v
```

### Hot-Reload Development

The manifest ingestion service watches the `manifests/` directory. Any changes are automatically detected and reloaded:

```bash
# Edit a manifest
vim manifests/agents/journaler/agent.yml

# Changes are auto-detected (check logs)
make logs-manifest

# Verify changes
curl http://localhost:8082/registry/manifest/Agent/journaler
```

---

## 📂 Project Structure

```
Cortex-Prime-MK1/
├── services/                      # Microservices
│   ├── manifest_ingestion/        # ✅ Manifest parser & registry
│   │   ├── main.py               # FastAPI app
│   │   ├── parsers/              # YAML/Markdown parsers
│   │   ├── models/               # Pydantic schemas
│   │   ├── registry/             # Manifest registry
│   │   ├── context_variables.py  # Variable resolver
│   │   ├── hotreload.py          # Filesystem watcher
│   │   ├── settings.yml          # Service configuration
│   │   └── tests/                # Test suite (25 tests)
│   │
│   ├── runtime_executor/          # 🚧 Sandboxed execution
│   │   ├── executors/            # Docker/Python/Bash executors
│   │   └── settings.yml          # Executor configuration
│   │
│   └── agent-lib/                 # 🚧 C++ arbiter core
│
├── manifests/                     # Declarative entity definitions
│   ├── agents/                   # Agent manifests
│   ├── tools/                    # Tool manifests
│   ├── relics/                   # Relic manifests
│   └── workflow/                 # Workflow manifests
│
├── docs/                          # Documentation
│   ├── ROADMAP.md                # Phase 0-5 development plan
│   ├── PROGRESS.md               # Current status
│   ├── INTEGRATION_TEST_RESULTS.md
│   └── manifests.md              # Manifest format guide
│
├── docker-compose.yml             # Service orchestration
├── Makefile                       # Development automation
├── .env.template                  # Environment configuration template
└── README.md                      # This file
```

---

## 📚 Documentation

- **[ROADMAP.md](docs/ROADMAP.md)** - Phase 0-5 development roadmap
- **[PROGRESS.md](docs/PROGRESS.md)** - Current development status
- **[FEATURES.md](services/manifest_ingestion/FEATURES.md)** - Detailed feature documentation
- **[INTEGRATION_TEST_RESULTS.md](docs/INTEGRATION_TEST_RESULTS.md)** - Test results
- **[TODO.md](services/agent-lib/TODO.md)** - Priority task tracking

---

## 🗺️ Roadmap

### Phase 0: Foundation Layer (33% Complete)

- [x] **Manifest Ingestion Pipeline** - Parse, validate, manage manifests
- [x] **Context Variable System** - Dynamic runtime variable resolution
- [ ] **Runtime Executor** - Sandboxed tool execution
- [ ] **First Relic** - Reference implementation pattern
- [ ] **Layered Directives** - Dynamic agent behavior modulation
- [ ] **Memory & Persistence** - State management across sessions

### Phase 1: Cognitive Enhancement
- Advanced error handling
- Expanded tool library
- Multi-step task decomposition

### Phase 2: Emergent Coordination
- Message bus integration (NATS/RabbitMQ)
- Inter-agent communication
- Collaborative task execution

### Phase 3: Observability & Optimization
- Unified logging & metrics
- Performance profiling
- Adaptive resource allocation

### Phase 4: Advanced Relics
- Vector knowledge bases
- ML model integration
- API abstraction layers

### Phase 5: Self-Modification
- Agent self-reflection
- Automated manifest generation
- Meta-learning strategies

---

## 🤝 Contributing

This is a personal research project following the **Himothy Covenant** principles. While not currently accepting external contributions, feel free to:

- **Fork** the repository for your own experiments
- **Open issues** for bugs or questions
- **Star** the repo if you find it interesting

---

## 📊 Status & Metrics

**Current Phase:** 0 - Foundation Layer  
**Completion:** 33% (2/6 core features)  
**Test Coverage:** 33/33 tests passing (100%)  
**Services:** 2 configured, 1 production-ready  
**Last Updated:** October 2025

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- Pydantic - Data validation
- Docker - Containerization
- Watchdog - Filesystem monitoring
- Neo4j - Graph database
- Redis - Caching

---

**"The Great Work continues."** 🏛️