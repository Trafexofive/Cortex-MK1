# 🏛️ Cortex-Prime MK1

> **"The distance between thought and action, minimized."**

A sovereign AI orchestration platform built on the **Himothy Covenant** principles. Cortex-Prime MK1 enables declarative, composable AI agents through hot-reloadable YAML manifests, fractal imports, context-aware variables, and containerized execution.

[![Manifests](https://img.shields.io/badge/manifests-23%20active-purple)]()
[![Tests](https://img.shields.io/badge/tests-33%2F33%20passing-brightgreen)]()
[![Phase](https://img.shields.io/badge/Phase%200-Foundation-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 Table of Contents

- [What is Cortex-Prime MK1?](#-what-is-cortex-prime-mk1)
- [Core Concepts](#-core-concepts)
- [Architecture](#%EF%B8%8F-architecture)
- [Quick Start](#-quick-start)
- [Manifest System](#-manifest-system)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)

---

## 🎯 What is Cortex-Prime MK1?

Cortex-Prime MK1 is a **declarative AI orchestration platform** that treats agents, tools, services, and entire stacks as composable, version-controlled manifests.

### Design Principles

**Declarative Reality** - Define what you want, not how to build it. YAML manifests specify agents, tools, relics (services), and monuments (complete stacks).

**Fractal Composability** - Everything imports everything. Agents import tools. Tools import agents. Relics import workflows. Monuments orchestrate it all.

**Hot-Reload by Default** - Change a manifest file, see it live. No rebuilds, no restarts (where possible).

**Context Awareness** - Variables like `$TIMESTAMP`, `$AGENT_NAME`, `$SESSION_ID` resolve dynamically at runtime, enabling adaptive behavior.

**Container-Native** - All builds, tests, and execution happen inside containers. Your host stays clean.

**FAAFO Engineering** - Fuck Around And Find Out. Fast iteration, bold experiments, emergent intelligence.

---

## 🧩 Core Concepts

### Manifest Types

Cortex-Prime uses a **fractal hierarchy** of manifest types, each serving different scales of complexity:

#### 🔧 **Tools**
Atomic, stateless capabilities. Execute single tasks with minimal dependencies.
```yaml
kind: Tool
name: "file_reader"
executor: "python"
script: "./scripts/read_file.py"
```

#### 🏺 **Relics**
Self-contained services with APIs. Can be local containers or remote endpoints.
```yaml
kind: Relic
name: "vector_store"
service:
  type: "docker-compose"
  compose_file: "./docker-compose.yml"
endpoints:
  embed: "http://vector-store:8004/embed"
```

#### 🤖 **Agents**
Intelligent entities that use tools and relics. Can import other agents.
```yaml
kind: Agent
name: "code_reviewer"
import:
  tools: ["static_analyzer", "git_diff"]
  relics: ["code_search_engine"]
  agents: ["syntax_checker", "security_auditor"]
```

#### 📜 **Workflows**
Multi-step orchestration with conditional logic, loops, and parallelization.
```yaml
kind: Workflow
name: "ci_pipeline"
steps:
  - name: "test"
    parallel: ["unit_tests", "integration_tests"]
  - name: "deploy"
    depends_on: ["test"]
```

#### 🏛️ **Monuments**
Complete systems composed of multiple relics, agents, and workflows. Think "entire search engine" or "distributed CI/CD platform."
```yaml
kind: Monument
name: "deep_search_stack"
relics:
  - whoogle
  - searxng
  - vector_store
  - crawler
agents:
  - query_agent
  - synthesis_agent
workflows:
  - search_pipeline
```

#### 🔮 **Amulets**
Reusable configuration and context bundles. Define once, import everywhere.
```yaml
kind: Amulet
name: "production_llm_config"
cognitive_engine:
  provider: "google"
  model: "gemini-1.5-pro"
  temperature: 0.3
```

### Key Features

**🔥 Fractal Import System** - Any manifest can import any other manifest. Build complex systems from simple primitives.

**🔄 Hot-Reload Everything** - Change a YAML file, see it live. Filesystem watchers auto-reload manifests.

**🧬 Context Variables** - 22+ built-in variables (`$TIMESTAMP`, `$AGENT_NAME`, `$SESSION_ID`) plus custom resolvers.

**📦 Container-Native** - All execution happens in Docker. Zero pollution on your host machine.

**🧪 Test-Driven** - 33/33 tests passing. Integration tests for every service.

**🎯 Settings.yml Pattern** - Every service has a centralized config file with environment overrides.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Cortex-Prime MK1 Stack                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │  Manifest        │         │  Runtime         │           │
│  │  Ingestion       │◄────────┤  Executor        │           │
│  │  (FastAPI)       │         │  (Sandboxed)     │           │
│  │  Port: 8082      │         │  Port: 8083      │           │
│  └────────┬─────────┘         └──────────────────┘           │
│           │                                                    │
│           │ YAML Manifests (23 active)                       │
│           ▼                                                    │
│  ┌──────────────────────────────────────────────┐            │
│  │  Manifest Registry                           │            │
│  │  ├─ Agents (hierarchical, composable)       │            │
│  │  ├─ Tools (atomic capabilities)             │            │
│  │  ├─ Relics (service wrappers)               │            │
│  │  ├─ Workflows (orchestration)               │            │
│  │  ├─ Monuments (complete stacks)             │            │
│  │  └─ Amulets (config bundles)                │            │
│  └──────────────────────────────────────────────┘            │
│                                                                │
│  ┌──────────────────────────────────────────────┐            │
│  │  Infrastructure Services                     │            │
│  │  ├─ Neo4j (graph DB, ports 7474/7687)       │            │
│  │  ├─ Redis (cache/state, port 6379)          │            │
│  │  └─ PostgreSQL (relational, port 5432)      │            │
│  └──────────────────────────────────────────────┘            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Service Matrix

| Service | Purpose | Port | Status | Tests |
|---------|---------|------|--------|-------|
| **Manifest Ingestion** | Parse, validate, manage manifests | 8082 | ✅ Production | 25/25 |
| **Runtime Executor** | Sandboxed tool execution | 8083 | 🚧 Development | 8/8 |
| **Chat Test** | Streaming protocol testing UI | 8888 | ✅ Production | - |
| **Neo4j** | Knowledge graph & relationships | 7474/7687 | ⚙️ Ready | - |
| **Redis** | Caching & session state | 6379 | ⚙️ Ready | - |
| **PostgreSQL** | Relational data store | 5432 | ⚙️ Ready | - |

### Data Flow

1. **Manifest Creation** - User writes YAML manifest
2. **Hot-Reload** - Filesystem watcher detects change
3. **Validation** - Pydantic schemas validate structure
4. **Context Resolution** - Variables like `$TIMESTAMP` resolved
5. **Registry Update** - Manifest stored in-memory registry
6. **Execution** - Runtime executor sandboxes tool/agent execution
7. **State Persistence** - Results cached in Redis/Neo4j

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** v2.0+
- **Make** (GNU Make 4.0+)
- **curl** & **jq** (for API testing)

### 60-Second Setup

```bash
# Clone the repository
git clone https://github.com/Trafexofive/Cortex-Prime-MK1.git
cd Cortex-Prime-MK1

# Configure environment
cp .env.template .env
# Edit .env and add your API keys (Google AI, etc.)

# Build and start entire stack
make setup

# Verify services
make health
```

### Try the Chat Test Service (New! 🎉)

Experience the streaming protocol with a live chat interface:

```bash
# Start the chat service
./chat.sh start

# Open browser
http://localhost:8888

# Try a query like:
# "What is 42 + 8?"
# "Tell me about AI"
# "Search arXiv for quantum computing"
```

Watch real-time streaming with visual protocol elements:
- 💭 **Thoughts** - Agent reasoning (yellow)
- 🔄 **Actions** - Tool execution (blue)
- 📝 **Response** - Final answer (green)

See [CONTAINERIZED_CHAT_READY.md](CONTAINERIZED_CHAT_READY.md) for complete guide.

### Verify Installation

```bash
# Check manifest ingestion service
curl http://localhost:8082/health
# {"status":"healthy","service":"manifest-ingestion","uptime":123.45}

# View registry status
curl http://localhost:8082/registry/status | jq
# {
#   "total_manifests": 23,
#   "agents": 8,
#   "tools": 10,
#   "relics": 3,
#   "workflows": 2
# }

# Force sync manifests from filesystem
make sync

# Follow service logs
make logs-manifest
```

### Your First Manifest

Create `manifests/agents/hello/agent.yml`:

```yaml
kind: Agent
version: "1.0"
name: "hello_agent"
summary: "My first Cortex agent"
author: "YOUR_NAME"
state: "unstable"

persona:
  agent: "./prompts/agent.md"

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"
  parameters:
    temperature: 0.7

import:
  tools:
    - "filesystem"

environment:
  variables:
    WORKSPACE: "$HOME/workspace/$AGENT_NAME"
```

The manifest is automatically detected and loaded within seconds. Check the registry:

```bash
curl http://localhost:8082/registry/manifest/Agent/hello_agent | jq
```

---

## 📜 Manifest System

### Fractal Composability

The true power of Cortex-Prime is **cross-manifest imports**:

```yaml
# Agent imports tools and other agents
kind: Agent
name: "senior_developer"
import:
  tools: ["git", "docker", "pytest"]
  agents: ["code_reviewer", "documentation_writer"]
  relics: ["ci_server", "artifact_storage"]
```

```yaml
# Tool imports an agent for intelligent processing
kind: Tool
name: "smart_refactor"
executor: "docker"
import:
  agents: ["syntax_analyzer"]  # Tool uses an agent!
```

```yaml
# Relic imports workflows for automation
kind: Relic
name: "auto_scaling_cluster"
import:
  workflows: ["health_check_loop", "scale_decision"]
```

This creates a **fractal hierarchy** where complexity emerges from simple, composable primitives.

### Context Variables (22+ Built-in)

Manifests support dynamic variables that resolve at runtime:

**Temporal:**
- `$TIMESTAMP` - Current UTC timestamp (ISO 8601)
- `$DATE`, `$TIME`, `$YEAR`, `$MONTH`, `$DAY`

**Identity:**
- `$AGENT_ID`, `$AGENT_NAME` - Agent identity
- `$TOOL_ID`, `$TOOL_NAME` - Tool identity
- `$SESSION_ID`, `$USER_ID` - Session context

**Environment:**
- `$HOME`, `$USER`, `$PWD`, `$HOSTNAME`

**Execution State:**
- `$ITERATION_COUNT`, `$CONFIDENCE`, `$ERROR_COUNT`

**Example:**
```yaml
environment:
  variables:
    LOG_DIR: "/logs/$AGENT_NAME/$SESSION_ID"
    WORKSPACE: "$HOME/cortex/$DATE"
    # Resolves to: /logs/senior_developer/abc123/
    #              /home/cortex/2025-01-15/
```

### API Endpoints

**Manifest Ingestion Service** - `http://localhost:8082`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/registry/status` | GET | Registry statistics (counts, manifest types) |
| `/registry/manifest/{kind}/{name}` | GET | Retrieve specific manifest |
| `/registry/agents` | GET | List all agent manifests |
| `/registry/tools` | GET | List all tool manifests |
| `/registry/relics` | GET | List all relic manifests |
| `/registry/sync` | POST | Force filesystem sync |
| `/manifests/upload` | POST | Upload manifest file |
| `/manifests/validate` | POST | Validate manifest without storing |
| `/docs` | GET | Interactive OpenAPI documentation |

---

## 🛠️ Development

### Makefile Commands (The Control Panel)

```bash
# ============ Quick Start ============
make setup              # Build images + start stack + sync manifests
make up                 # Start all services in detached mode
make down               # Stop and remove all services
make restart            # Restart services (down + up)

# ============ Monitoring ============
make status             # Show service status (ps)
make health             # Check all service health endpoints
make logs               # Follow all service logs
make logs-manifest      # Follow manifest service logs only
make logs-runtime       # Follow runtime executor logs only

# ============ Testing ============
make test               # Run all test suites
make test-manifest      # Test manifest ingestion service
make test-runtime       # Test runtime executor
make test-integration   # Run integration tests

# ============ Manifest Operations ============
make sync               # Force manifest sync from filesystem
make validate           # Validate all manifests against schemas

# ============ Building ============
make build              # Build images (uses Docker cache)
make rebuild            # Build images (no cache, clean build)
make re                 # Rebuild + restart + logs

# ============ Debugging ============
make ssh service=<name>       # Interactive shell into service
make exec svc=<name> cmd="<cmd>" # Execute command in service

# Examples:
make ssh service=manifest_ingestion
make exec svc=manifest_ingestion cmd="pytest tests/ -v"

# ============ Cleaning ============
make clean              # Remove containers and networks
make fclean             # Remove containers, volumes, networks
make prune              # Full Docker system prune (nuclear option)
```

### Hot-Reload Development Workflow

The manifest ingestion service watches `manifests/` with filesystem monitoring:

```bash
# Start the stack
make up

# Edit a manifest in your favorite editor
vim manifests/agents/code_reviewer/agent.yml

# Changes auto-detected within 1-2 seconds (check logs)
make logs-manifest
# [2025-01-15 10:23:45] INFO: Detected change: agents/code_reviewer/agent.yml
# [2025-01-15 10:23:45] INFO: Reloading manifest: code_reviewer
# [2025-01-15 10:23:45] INFO: Validation passed
# [2025-01-15 10:23:45] INFO: Registry updated

# Verify changes via API
curl http://localhost:8082/registry/manifest/Agent/code_reviewer | jq
```

### Running Tests

```bash
# All tests (33/33 passing)
make test

# Specific service
make test-manifest

# Inside container (for debugging)
docker exec -it cortex-manifest-ingestion pytest tests/ -v --tb=short

# Integration tests
make test-integration
```

### Settings.yml Pattern

Every service follows the same configuration pattern:

```yaml
# services/manifest_ingestion/settings.yml
service:
  name: "ManifestIngestion"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 8082
  log_level: "INFO"

registry:
  auto_sync: true
  watch_directories: true
  cache_enabled: true

hotreload:
  enabled: true
  debounce_seconds: 0.5
  patterns: ["*.yml", "*.yaml", "*.md"]
```

Override via environment variables:
```bash
export MANIFEST_INGESTION_LOG_LEVEL="DEBUG"
export MANIFEST_INGESTION_HOTRELOAD_ENABLED="false"
```

---

## 📂 Project Structure

```
Cortex-Prime-MK1/
├── services/                          # Microservices (container-native)
│   ├── manifest_ingestion/            # ✅ Manifest parser & registry
│   │   ├── main.py                   # FastAPI application
│   │   ├── parsers/                  # YAML/Markdown parsers
│   │   │   ├── base.py              # Abstract parser interface
│   │   │   ├── yaml_parser.py       # YAML manifest parser
│   │   │   └── markdown_parser.py   # MD frontmatter parser
│   │   ├── models/                   # Pydantic schemas
│   │   │   ├── agent.py             # Agent manifest schema
│   │   │   ├── tool.py              # Tool manifest schema
│   │   │   ├── relic.py             # Relic manifest schema
│   │   │   ├── workflow.py          # Workflow manifest schema
│   │   │   ├── monument.py          # Monument manifest schema
│   │   │   └── amulet.py            # Amulet manifest schema
│   │   ├── registry/                 # In-memory manifest registry
│   │   │   ├── registry.py          # Core registry logic
│   │   │   └── validation.py        # Dependency validation
│   │   ├── context_variables.py      # Variable resolution engine
│   │   ├── hotreload.py              # Filesystem watcher
│   │   ├── settings.yml              # Service configuration
│   │   ├── requirements.txt          # Python dependencies
│   │   ├── Dockerfile                # Container image
│   │   └── tests/                    # Test suite (25/25 passing)
│   │       ├── test_parsers.py
│   │       ├── test_registry.py
│   │       ├── test_context.py
│   │       └── test_hotreload.py
│   │
│   ├── runtime_executor/              # 🚧 Sandboxed execution engine
│   │   ├── main.py                   # FastAPI application
│   │   ├── executors/                # Execution strategies
│   │   │   ├── docker_executor.py   # Docker-based sandboxing
│   │   │   ├── python_executor.py   # Python script runner
│   │   │   └── bash_executor.py     # Shell command runner
│   │   ├── streaming_protocol_parser.py # ✅ Token-by-token parser
│   │   ├── agent_loop_executor.py    # ✅ Agent execution loop
│   │   ├── models/
│   │   │   └── agent_execution_protocol.py # ✅ Execution models
│   │   ├── sandbox.py                # Isolation & security
│   │   ├── settings.yml              # Service configuration
│   │   └── tests/                    # Test suite (8/8 passing)
│   │
│   ├── chat_test/                     # ✅ Streaming protocol test UI
│   │   ├── chat_test_service.py      # FastAPI + embedded chat UI
│   │   ├── runtime_executor/         # Parser dependency
│   │   │   └── streaming_protocol_parser.py
│   │   ├── requirements.txt          # Dependencies
│   │   ├── Dockerfile                # Container image
│   │   ├── README.md                 # Quick start
│   │   └── DOCKER_GUIDE.md           # Complete guide
│   │
│   └── agent-lib/                     # 🔮 Future: C++ arbiter core
│
├── manifests/                         # Declarative entity definitions (23 manifests)
│   ├── agents/                       # Agent manifests
│   │   ├── journaler/                # Example: journaling agent
│   │   │   ├── agent.yml
│   │   │   └── prompts/agent.md
│   │   ├── researcher/               # Example: research agent
│   │   ├── code_reviewer/            # Example: code review agent
│   │   └── orchestrator/             # Example: meta-orchestrator
│   │
│   ├── tools/                        # Tool manifests
│   │   ├── filesystem/               # File operations
│   │   ├── git/                      # Git commands
│   │   ├── docker/                   # Docker operations
│   │   └── web_scraper/              # Web scraping
│   │
│   ├── relics/                       # Relic (service) manifests
│   │   ├── vector_store/             # Vector DB service
│   │   ├── llm_gateway/              # Multi-provider LLM proxy
│   │   └── crawler/                  # Web crawler service
│   │
│   ├── workflows/                    # Workflow manifests
│   │   ├── research_pipeline/        # Multi-step research workflow
│   │   └── ci_pipeline/              # CI/CD automation
│   │
│   └── monuments/                    # Monument (stack) manifests
│       └── deep_search/              # Complete search engine stack
│
├── docs/                              # Documentation
│   ├── ROADMAP.md                    # Phase 0-5 development plan
│   ├── PROGRESS.md                   # Current development status
│   ├── manifests.md                  # Complete manifest reference
│   ├── FRACTAL_DESIGN.md             # Fractal composability principles
│   ├── WORKFLOW_DESIGN.md            # Workflow orchestration design
│   └── INTEGRATION_TEST_RESULTS.md   # Test results & coverage
│
├── infra/                             # Infrastructure configs
│   ├── docker-compose.yml            # Service orchestration
│   ├── nginx/                        # Reverse proxy configs
│   └── monitoring/                   # Prometheus/Grafana (future)
│
├── scripts/                           # Utility scripts
│   ├── init_db.sh                    # Database initialization
│   ├── backup.sh                     # Backup manifests & data
│   └── health_check.sh               # Service health monitoring
│
├── testing/                           # Integration tests
│   ├── test_e2e.py                   # End-to-end workflows
│   └── test_manifest_flow.py         # Manifest lifecycle
│
├── examples/                          # Example workflows & use cases
│   ├── simple_agent/                 # Minimal agent example
│   ├── tool_chaining/                # Tool composition example
│   └── monument_deployment/          # Full stack deployment
│
├── .env.template                      # Environment configuration template
├── docker-compose.yml                 # Main service orchestration
├── Makefile                           # Development automation (20+ commands)
├── settings.yml                       # Global stack configuration
└── README.md                          # This file
```

### Key Directories Explained

**`services/`** - Each microservice is fully self-contained with its own Dockerfile, settings.yml, tests, and requirements.txt. Zero coupling.

**`manifests/`** - Version-controlled, declarative entity definitions. Hot-reloaded by the ingestion service.

**`docs/`** - Comprehensive documentation including design philosophy, API reference, and progress tracking.

**`infra/`** - Infrastructure-as-code. Docker Compose orchestration, reverse proxy configs, future monitoring.

**Build artifacts, caches, and virtualenvs stay INSIDE containers.** Your host filesystem remains pristine.

---

## 📚 Documentation

### Core Documentation

- **[manifests.md](docs/manifests.md)** - Complete manifest reference with schemas, examples, and best practices
- **[ROADMAP.md](docs/ROADMAP.md)** - Phase 0-5 development roadmap with technical milestones
- **[PROGRESS.md](docs/PROGRESS.md)** - Current development status and completed features
- **[FRACTAL_DESIGN.md](docs/FRACTAL_DESIGN.md)** - Fractal composability philosophy and import patterns
- **[WORKFLOW_DESIGN.md](docs/WORKFLOW_DESIGN.md)** - Workflow orchestration and execution design
- **[INTEGRATION_TEST_RESULTS.md](docs/INTEGRATION_TEST_RESULTS.md)** - Test coverage and results

### New: Streaming Protocol & Chat

- **[STREAMING_PROTOCOL.md](docs/STREAMING_PROTOCOL.md)** - Complete streaming protocol specification
- **[AGENT_EXECUTION_PROTOCOL.md](docs/AGENT_EXECUTION_PROTOCOL.md)** - Execution protocol with DAG scheduling
- **[CONTAINERIZED_CHAT_READY.md](CONTAINERIZED_CHAT_READY.md)** - Chat test service quick start
- **[CHAT_TEST_README.md](CHAT_TEST_README.md)** - Complete chat testing guide
- **[services/chat_test/DOCKER_GUIDE.md](services/chat_test/DOCKER_GUIDE.md)** - Docker deployment guide

---

## 🗺️ Roadmap

### Phase 0: Foundation Layer (In Progress)

**Completed:**
- [x] Manifest ingestion pipeline (YAML + Markdown parsers)
- [x] Schema validation (Pydantic models for all manifest types)
- [x] Hot-reload system (filesystem watcher with debouncing)
- [x] Context variable system (22 built-in variables + custom resolvers)
- [x] Manifest registry (in-memory with dependency tracking)
- [x] RESTful API (FastAPI with OpenAPI docs)
- [x] Test suite (33/33 tests passing)
- [x] **Streaming protocol parser** (token-by-token XML+JSON parsing)
- [x] **Agent execution protocol** (DAG-based parallel action execution)
- [x] **Chat test service** (containerized web UI for protocol testing)
- [x] **Comprehensive testing infrastructure** (manifest validation, tool testing)

**In Progress:**
- [ ] Runtime executor integration (connect parser to execution engine)
- [ ] First production relic (vector store or LLM gateway)
- [ ] Memory & persistence layer (Neo4j integration)
- [ ] Layered directives (dynamic agent behavior modulation)

### Phase 1: Cognitive Enhancement
- Advanced error handling with retry strategies
- Expanded tool library (20+ production tools)
- Multi-step task decomposition engine
- Confidence scoring & self-assessment

### Phase 2: Emergent Coordination
- Message bus integration (NATS or RabbitMQ)
- Inter-agent communication protocol
- Collaborative task execution
- Distributed workflow orchestration

### Phase 3: Observability & Optimization
- Unified logging with structured output
- Prometheus metrics & Grafana dashboards
- Performance profiling & bottleneck detection
- Adaptive resource allocation

### Phase 4: Advanced Relics & Monuments
- Production-ready monument examples
- Vector knowledge bases with RAG
- ML model integration (inference + fine-tuning)
- API abstraction layers for external services

### Phase 5: Self-Modification
- Agent self-reflection & introspection
- Automated manifest generation
- Meta-learning strategies
- Emergent tool creation

**Current Status:** Phase 0 - 40% complete

---

## 🎯 Use Cases

What you can build with Cortex-Prime:

**Research Assistant Monument** - Search engine + crawler + vector store + synthesis agent. Ask complex questions, get cited answers from multiple sources.

**Code Review Agent** - Imports static analysis tools + git diff tool + security scanner. Reviews PRs with context-aware feedback.

**Personal Knowledge Base** - Ingestion agents + graph DB + retrieval agents. Query your personal notes, papers, and documents.

**CI/CD Pipeline Workflow** - Test tools + build tools + deploy agents. Orchestrate complex multi-stage pipelines.

**Self-Hosting Stack** - Monument definition for entire infrastructure. Deploy complete systems with one manifest.

---

## 🤝 Contributing

This is a personal research project exploring autonomous AI architectures. While external contributions aren't currently accepted, you're welcome to:

- **Fork** the repository for your own experiments
- **Open issues** for bugs, questions, or feature suggestions
- **Star** the repo if you find the ideas interesting
- **Share** your own manifest designs and use cases

---

## 📊 Current Metrics

**Development Phase:** 0 (Foundation Layer)  
**Phase Completion:** 55%  
**Active Manifests:** 11 (all validated and passing)  
**Test Coverage:** 33/33 passing (100%)  
**Production Services:** 2 (Manifest Ingestion, Chat Test)  
**Services in Development:** 1 (Runtime Executor)  
**Lines of Code:** ~15,600 (excluding tests/docs)  
**Documentation Pages:** 11 comprehensive guides  
**New Features:** Streaming protocol parser, agent execution engine, chat UI

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🙏 Built With

**Core Stack:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation and settings
- [Docker](https://www.docker.com/) - Containerization
- [Watchdog](https://pythonhosted.org/watchdog/) - Filesystem monitoring

**Infrastructure:**
- [Neo4j](https://neo4j.com/) - Graph database
- [Redis](https://redis.io/) - Cache and state management
- [PostgreSQL](https://www.postgresql.org/) - Relational data store

**AI/LLM Providers:**
- Google Gemini
- Groq
- Ollama (local)

---

**"The Great Work continues."** 🏛️

---

## Quick Links

- [API Documentation](http://localhost:8082/docs) (when running)
- [Manifest Registry Status](http://localhost:8082/registry/status) (when running)
- [Repository](https://github.com/Trafexofive/Cortex-Prime-MK1)
- [Issues](https://github.com/Trafexofive/Cortex-Prime-MK1/issues)