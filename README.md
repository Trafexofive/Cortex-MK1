# 🏛️ Cortex-Prime MK1

> **"The distance between thought and action, minimized."**

A sovereign AI orchestration platform enabling production-grade agentic systems through declarative manifests, streaming protocol execution, and fractal composability. Born from **agent-lib**, evolved into a complete framework for building, deploying, and orchestrating intelligent agents.

[![Agent-Lib](https://img.shields.io/badge/agent--lib-v1.2-blue)]()
[![Protocol](https://img.shields.io/badge/streaming-XML%2BJSON-purple)]()
[![Manifests](https://img.shields.io/badge/manifests-modern-green)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 Table of Contents

- [What is Cortex-Prime MK1?](#-what-is-cortex-prime-mk1)
- [Quick Start](#-quick-start)
- [Agent-Lib: The Core](#-agent-lib-the-core)
- [Manifest System](#-manifest-system)
- [Architecture](#%EF%B8%8F-architecture)
- [Services](#-services)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Roadmap](#-roadmap)

---

## 🎯 What is Cortex-Prime MK1?

Cortex-Prime MK1 is a **production-ready agentic AI framework** that treats agents, tools, services, and workflows as composable, self-contained manifests. At its heart is **agent-lib**, a high-performance C++ runtime that executes agents using a streaming XML+JSON fusion protocol.

### Why Cortex-Prime?

**From Daily Driver to Framework** - agent-lib was originally built as a personal daily driver for running AI agents. It evolved into Cortex-Prime MK1, a complete platform that others can use to build their own agentic systems.

**Streaming Protocol First** - Unlike traditional request-response systems, Cortex-Prime uses a **streaming protocol** where agents think, act, and respond in real-time through structured XML+JSON blocks.

**Manifest-Driven Everything** - Agents, tools, relics (services), and even complete stacks are defined in YAML manifests that are modular, composable, and self-contained.

**Production-Grade Execution** - Built in C++ for performance, with Python tooling for flexibility. Real streaming inference, proper context management, and robust error handling.

### Design Principles

**Declarative Reality** - Define what you want, not how to build it. Manifests specify agents, tools, relics (services), and workflows.

**Fractal Composability** - Everything imports everything. Agents import tools. Tools can invoke agents. Relics provide infrastructure. All self-contained and modular.

**CAG Over RAG** - Context-Augmented Generation is first-class. Full context and history are maintained. If you need RAG, build it as a tool or relic.

**Streaming Execution** - Agents don't wait for full responses. They stream thoughts, actions, and responses incrementally using the XML+JSON fusion protocol.

**Self-Contained Modules** - Every agent, tool, and relic is a complete, isolated unit with its own config, scripts, and dependencies.

---

## 🤖 Agent-Lib: The Core

**agent-lib** is the beating heart of Cortex-Prime MK1. Originally a personal daily-driver for AI agents, it's now a production-ready C++ runtime that powers the entire platform.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT-LIB v1.2                           │
│              Streaming XML+JSON Fusion Protocol             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │ CLI Binary   │    │ HTTP Server  │   │  Agent Core  │  │
│  │ ./agent-bin  │───▶│ FastAPI/C++  │──▶│   Runtime    │  │
│  └──────────────┘    └──────────────┘   └──────┬───────┘  │
│                                                  │          │
│         ┌────────────────────────────────────────┘          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Manifest Loader (Modern YAML Parser)                 │  │
│  │ ├─ Agent manifests (cognitive config)                │  │
│  │ ├─ Tool manifests (capabilities)                     │  │
│  │ ├─ Relic manifests (services)                        │  │
│  │ └─ Auto-import from std/manifests                    │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│                 ▼                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Streaming Protocol Parser                            │  │
│  │ ├─ <thought> blocks - Internal reasoning             │  │
│  │ ├─ <action> blocks - Tool/agent invocations          │  │
│  │ ├─ <response> blocks - User-facing messages          │  │
│  │ └─ Non-terminating flag support                      │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│                 ▼                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Action Executor                                       │  │
│  │ ├─ Tool execution (Python/Node/Shell/Docker)         │  │
│  │ ├─ Sub-agent delegation (streaming passthrough)      │  │
│  │ ├─ Relic API calls (HTTP/gRPC)                       │  │
│  │ ├─ Internal actions (system_clock, variables)        │  │
│  │ └─ Result storage & context injection                │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│                 ▼                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Context Manager                                       │  │
│  │ ├─ Full conversation history (CAG, not RAG)          │  │
│  │ ├─ Action results                                    │  │
│  │ ├─ Context feeds (on-demand data injection)          │  │
│  │ ├─ Variable expansion ($TIMESTAMP, $AGENT_NAME, etc) │  │
│  │ └─ Environment variables                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ LLM Gateway Integration                               │  │
│  │ └─ Streaming inference (Google Gemini, Groq, etc)    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

#### ✅ **Streaming Protocol Execution**
Real-time XML+JSON fusion protocol that enables agents to think, act, and respond incrementally:

```xml
<thought>
I need to check the current time before responding.
</thought>

<action>
{
  "name": "system_clock",
  "parameters": {
    "format": "ISO8601",
    "timezone": "UTC"
  }
}
</action>

<response non_terminating="false">
The current time is 2025-01-15 14:23:45 UTC. How can I help you?
</response>
```

#### ✅ **Modern Manifest System**
Self-contained, modular manifests for agents, tools, and relics:

```yaml
kind: Agent
version: "1.0"
name: "sage"
summary: "Research and knowledge advisor"

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-2.0-flash"
  parameters:
    temperature: 0.3
    max_tokens: 8192
    stream: true

import:
  tools:
    - "knowledge_retriever"
    - "fact_checker"

context_feeds:
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
```

#### ✅ **Tool System**
Tools are self-contained modules with their own manifests and executables:

```yaml
kind: Tool
version: "1.0"
name: "knowledge_retriever"

description: "Search knowledge base for information"

executor:
  runtime: "python"
  script: "./scripts/knowledge_retriever.py"

parameters:
  query:
    type: "string"
    required: true
  depth:
    type: "string"
    enum: ["quick", "deep"]
    default: "quick"
```

#### ✅ **Sub-Agent Delegation**
Agents can invoke other agents, streaming their responses:

```xml
<action>
{
  "name": "delegate_to_agent",
  "parameters": {
    "agent": "research_assistant",
    "prompt": "Find recent papers on quantum computing"
  }
}
</action>
```

#### ✅ **Context Feeds**
Dynamic data injection at runtime:

```yaml
context_feeds:
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      
  - id: "research_session"
    type: "on_demand"
    source:
      type: "tool"
      tool: "session_retriever"
```

#### ✅ **Internal Actions**
Built-in capabilities available to all agents:

- `system_clock` - Current timestamp with timezone support
- `agent_metadata` - Agent configuration and state
- `context_feed_manager` - Dynamic context injection
- `variable_manager` - Variable expansion and storage

### Build & Run

```bash
cd services/agent-lib

# Build binaries
make                 # Build both CLI and server
make bin            # Build CLI only
make server         # Build server only

# Run
./agent-bin -l config/agents/sage/agent.yml
./agent-server      # Start HTTP server (port 8090)

# Clean
make clean          # Remove binaries
make fclean         # Deep clean (includes build artifacts)
```

### Agent Manifests

Agent-lib includes production-ready agents in `config/agents/`:

- **sage** - Research and knowledge advisor (uses knowledge_retriever, fact_checker)
- **demurge** - Creative problem solver and system builder
- More coming...

### Extending Agent-Lib

Create your own agents by:

1. **Create manifest**: `config/agents/my_agent/agent.yml`
2. **Add system prompt**: `config/agents/my_agent/system-prompts/my_agent.md`
3. **Add tools** (optional): `config/agents/my_agent/tools/my_tool/tool.yml`
4. **Load and run**: `./agent-bin -l config/agents/my_agent/agent.yml`

---

## 📜 Manifest System

### Manifest Hierarchy

Cortex-Prime uses a **fractal hierarchy** of manifest types, each self-contained and modular:

#### 🔧 **Tools**
Atomic, stateless capabilities. Execute single tasks.

```yaml
kind: Tool
version: "1.0"
name: "fact_checker"

description: "Verify factual claims and check logical consistency"

executor:
  runtime: "python"
  script: "./scripts/fact_checker.py"

parameters:
  claim:
    type: "string"
    required: true
    description: "The claim to verify"
  
  check_sources:
    type: "boolean"
    default: true
    description: "Whether to verify against known sources"

output_schema:
  type: "object"
  properties:
    verified:
      type: "boolean"
    confidence:
      type: "number"
    sources:
      type: "array"
```

#### 🏺 **Relics**
Self-contained services with lifecycle management.

```yaml
kind: Relic
version: "1.0"
name: "vector_store"

description: "Persistent vector database for embeddings"

service:
  type: "docker-compose"
  compose_file: "./docker-compose.yml"
  health_check:
    endpoint: "http://localhost:8004/health"
    interval: 30
  auto_start: true

endpoints:
  embed: "http://vector-store:8004/embed"
  search: "http://vector-store:8004/search"

environment:
  variables:
    VECTOR_DIM: "768"
    INDEX_TYPE: "HNSW"
```

#### 🤖 **Agents**
Intelligent entities that use tools and relics.

```yaml
kind: Agent
version: "1.0"
name: "research_agent"

persona:
  agent: "./system-prompts/agent.md"

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"
  
  fallback:
    provider: "groq"
    model: "llama-3.1-70b-versatile"
  
  parameters:
    temperature: 0.7
    max_tokens: 4096
    stream: true

import:
  tools:
    - "web_search"
    - "knowledge_retriever"
  
  relics:
    - "vector_store"
  
  agents:
    - "fact_checker_agent"  # Sub-agent delegation

context_feeds:
  - id: "current_time"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"

environment:
  variables:
    WORKSPACE: "$HOME/research/$SESSION_ID"
```

#### 📜 **Workflows**
Multi-step orchestration (planned).

```yaml
kind: Workflow
version: "1.0"
name: "research_pipeline"

steps:
  - name: "gather"
    agent: "web_researcher"
    
  - name: "analyze"
    agent: "data_analyst"
    depends_on: ["gather"]
    
  - name: "synthesize"
    agent: "report_writer"
    depends_on: ["analyze"]
```

#### 🏛️ **Monuments**
Complete systems composed of multiple entities (planned).

```yaml
kind: Monument
version: "1.0"
name: "knowledge_platform"

relics:
  - vector_store
  - graph_database
  - search_engine

agents:
  - researcher
  - synthesizer
  - curator

workflows:
  - ingestion_pipeline
  - query_pipeline
```

### Manifest Location

Manifests are organized in two locations:

1. **Local** - `config/agents/`, `config/tools/`, etc. (agent-specific)
2. **Standard Library** - `std/manifests/` (shared across system)

```
services/agent-lib/
├── config/
│   ├── agents/
│   │   ├── sage/
│   │   │   ├── agent.yml
│   │   │   ├── system-prompts/
│   │   │   │   └── sage.md
│   │   │   └── tools/
│   │   │       ├── knowledge_retriever/
│   │   │       │   ├── tool.yml
│   │   │       │   └── scripts/
│   │   │       │       └── knowledge_retriever.py
│   │   │       └── fact_checker/
│   │   │           ├── tool.yml
│   │   │           └── scripts/
│   │   │               └── fact_checker.py
│   │   └── demurge/
│   │       └── agent.yml
│   │
│   └── relics/
│       └── (planned)

std/manifests/
├── agents/
├── tools/
├── relics/
├── workflows/
└── monuments/
```

### Fractal Composability

The true power is **cross-manifest imports**:

```yaml
# Agent imports tools and other agents
kind: Agent
name: "senior_developer"
import:
  tools: ["git", "docker", "pytest"]
  agents: ["code_reviewer", "documentation_writer"]
  relics: ["ci_server"]
```

```yaml
# Tool can invoke agents for intelligent processing
kind: Tool
name: "smart_refactor"
import:
  agents: ["syntax_analyzer"]
```

This creates a **fractal hierarchy** where complexity emerges from simple primitives.

---

## 🏗️ Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   Cortex-Prime MK1 Stack                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐         ┌──────────────────┐       │
│  │   Agent-Lib v1.2   │         │   LLM Gateway    │       │
│  │   (C++ Runtime)    │◄────────┤   (Multi-LLM)    │       │
│  │   Port: 8090       │ Stream  │   Port: 8081     │       │
│  └──────────┬─────────┘         └──────────────────┘       │
│             │                                                │
│             │ Manifests (YAML)                              │
│             ▼                                                │
│  ┌──────────────────────────────────────────┐              │
│  │  Manifest Registry                       │              │
│  │  ├─ Agents (cognitive profiles)          │              │
│  │  ├─ Tools (atomic capabilities)          │              │
│  │  ├─ Relics (service wrappers)           │              │
│  │  ├─ Workflows (orchestration)           │              │
│  │  └─ Monuments (complete stacks)         │              │
│  └──────────────────────────────────────────┘              │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │  Supporting Services (Optional)          │              │
│  │  ├─ Manifest Ingestion (FastAPI)         │              │
│  │  ├─ Runtime Executor (Sandboxed)         │              │
│  │  ├─ B-Line Dashboard (Next.js)           │              │
│  │  ├─ Neo4j (Graph DB)                     │              │
│  │  ├─ Redis (Cache/State)                  │              │
│  │  └─ PostgreSQL (Relational)              │              │
│  └──────────────────────────────────────────┘              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Core Components

#### **Agent-Lib** (Primary Runtime)
- **Language**: C++ for performance
- **Purpose**: Execute agents using streaming protocol
- **Key Features**: 
  - Real-time streaming inference
  - Tool execution (Python/Node/Shell/Docker)
  - Sub-agent delegation
  - Context feed management
  - Internal action system

#### **LLM Gateway** (AI Provider Abstraction)
- **Language**: Python (FastAPI)
- **Purpose**: Multi-provider LLM access with streaming
- **Providers**: Google Gemini, Groq, Ollama (local)
- **Free Tier**: Use Gemini for zero-cost inference

#### **Manifest Ingestion** (Optional, for hot-reload)
- **Language**: Python (FastAPI)
- **Purpose**: Parse, validate, and registry manifests
- **Features**: Filesystem watching, validation, dependency resolution

#### **Runtime Executor** (Optional, for distributed execution)
- **Language**: Python (FastAPI)
- **Purpose**: Sandboxed tool execution in containers
- **Use Case**: When you need isolation from agent process

### Data Flow

1. **User Input** → Agent-Lib CLI/Server
2. **Context Building** → Full history + context feeds + variables
3. **LLM Request** → Streaming inference via LLM Gateway
4. **Protocol Parsing** → Real-time XML+JSON block extraction
5. **Action Execution** → Tools, sub-agents, relics, internal actions
6. **Result Injection** → Results added to context
7. **Iteration** → Repeat until response or iteration cap
8. **User Output** → Final response delivered

### Execution Flow

```
User Input
    │
    ▼
┌─────────────────────┐
│  Agent-Lib Core     │
│  - Load manifest    │
│  - Build context    │
│  - Init conversation│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LLM Gateway        │
│  - Stream request   │
│  - Real-time tokens │
└──────────┬──────────┘
           │ Stream
           ▼
┌─────────────────────┐
│  Protocol Parser    │
│  - Extract <thought>│
│  - Extract <action> │
│  - Extract <response>│
└──────────┬──────────┘
           │
           ▼
     <action> found?
           │
      ┌────┴────┐
      │         │
     Yes       No
      │         │
      ▼         ▼
┌──────────┐  Output
│ Execute  │  Response
│ Action   │     │
│ (Tool/   │     │
│  Agent/  │     │
│  Relic)  │     │
└────┬─────┘     │
     │           │
     ▼           │
  Inject         │
  Result         │
     │           │
     └─────┬─────┘
           │
    Iteration++
           │
    Continue? (iteration < cap)
           │
      ┌────┴────┐
      │         │
     Yes       No
      │         │
      └────┐    └─→ End
           │
           ▼
      Repeat
```

---

## 🚀 Quick Start

### Prerequisites

- **Linux** (tested on Ubuntu/Debian)
- **C++ Compiler** (g++ 9.0+)
- **Python 3.8+**
- **Make** (GNU Make 4.0+)
- **Docker** (optional, for relics/services)

### 60-Second Setup (Agent-Lib Binary)

```bash
# Clone the repository
git clone https://github.com/Trafexofive/Cortex-Prime-MK1.git
cd Cortex-Prime-MK1/services/agent-lib

# Set your API key (required)
export LLM_GATEWAY_API_KEY="your-google-api-key"

# Build the agent binary
make

# Run an agent (interactive CLI)
./agent-bin -l config/agents/sage/agent.yml
```

**That's it.** You now have a fully functional AI agent running locally.

### Your First Interaction

```bash
./agent-bin -l config/agents/sage/agent.yml

> hello
[Streaming...]
Hello! I am Sage, ready to assist you with your inquiries. How can I help you today?

> what can you do?
[Streaming...]
I am Sage, a knowledgeable advisor designed to assist you with complex questions...
[Shows capabilities, tools, approach]

> /tools
Available tools:
  - fact_checker: Verify factual claims
  - knowledge_retriever: Search knowledge base

> /quit
Goodbye!
```

### CLI Flags

```bash
./agent-bin -h              # Show help
./agent-bin -l <path>       # Load manifest
./agent-bin -v              # Verbose logging
./agent-bin --stream        # Force streaming mode (default)
```

### Available Commands

While chatting with an agent:

```
/load <path>    - Load different agent manifest
/reload         - Reload current manifest
/stream on|off  - Toggle streaming mode
/tools          - List available tools
/info           - Show agent configuration
/clear          - Clear conversation history
/help           - Show command help
/quit or /exit  - Exit CLI
```

---

## 🔧 Services

Cortex-Prime is designed as a modular ecosystem. **Agent-lib is standalone**, but you can add supporting services for advanced features.

### Core Service (Required)

| Service | Purpose | Language | Port | Status |
|---------|---------|----------|------|--------|
| **Agent-Lib** | Agent execution runtime | C++ | 8090 | ✅ Production |
| **LLM Gateway** | Multi-provider LLM access | Python | 8081 | ✅ Production |

### Optional Services

| Service | Purpose | Language | Port | Status |
|---------|---------|----------|------|--------|
| **Manifest Ingestion** | Hot-reload & validation | Python | 8082 | ✅ Available |
| **Runtime Executor** | Distributed tool execution | Python | 8083 | ✅ Available |
| **B-Line Dashboard** | Web UI for manifests | Next.js | 3000 | ✅ Available |
| **Chat Test** | Protocol testing UI | Python | 8888 | ✅ Available |

### Infrastructure (Optional)

| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| **Neo4j** | Knowledge graph storage | 7474/7687 | ⚙️ Ready |
| **Redis** | Caching & state | 6379 | ⚙️ Ready |
| **PostgreSQL** | Relational storage | 5432 | ⚙️ Ready |

### Running Services

```bash
# Minimal (agent-lib only)
cd services/agent-lib && make && ./agent-bin -l config/agents/sage/agent.yml

# With LLM Gateway (for streaming inference)
cd services/llm_gateway && docker-compose up -d

# Full stack (all services)
cd /path/to/Cortex-Prime-MK1
docker-compose up -d
```

---

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

### Agent-Lib Development

```bash
cd services/agent-lib

# Build
make                # Build both CLI and server
make bin            # CLI only
make server         # Server only
make clean          # Remove binaries
make fclean         # Deep clean

# Run
./agent-bin -l config/agents/sage/agent.yml
./agent-server      # HTTP server on port 8090

# Test
make test           # Run all tests
./test_all_manifests.sh
```

### Docker Stack Development

```bash
# Quick commands
make up STACK=core      # Start core services
make up                 # Start full stack
make down               # Stop services
make restart            # Restart all
make rebuild            # No-cache rebuild

# Monitoring
make status             # Service status
make health             # Health checks
make logs               # All logs
make logs-manifest      # Specific service
make logs-runtime
make logs-agent-lib

# Testing
make test               # All tests
make test-manifest      # Specific service
make test-runtime
make test-integration

# Debugging
make ssh service=agent_lib          # Shell into container
make exec svc=agent_lib cmd="ls"    # Run command

# Cleaning
make clean              # Remove containers
make fclean             # Remove volumes too
make prune              # Nuclear option
```

### Creating Your Own Agent

1. **Create directory structure**:

```bash
mkdir -p config/agents/my_agent/system-prompts
mkdir -p config/agents/my_agent/tools
```

2. **Create agent manifest** (`config/agents/my_agent/agent.yml`):

```yaml
kind: Agent
version: "1.0"
name: "my_agent"
summary: "Your agent description"
author: "YOUR_NAME"
state: "unstable"

persona:
  agent: "./system-prompts/my_agent.md"

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-2.0-flash"
  parameters:
    temperature: 0.7
    max_tokens: 4096
    stream: true

import:
  tools: []

iteration_cap: 10
```

3. **Create system prompt** (`config/agents/my_agent/system-prompts/my_agent.md`):

```markdown
# My Agent

You are My Agent, a helpful assistant.

## Core Capabilities
- Capability 1
- Capability 2

## Response Format
Use the streaming protocol:
- <thought> for internal reasoning
- <action> for tool calls
- <response> for user messages
```

4. **Load and test**:

```bash
./agent-bin -l config/agents/my_agent/agent.yml
```

### Creating Custom Tools

1. **Create tool directory**:

```bash
mkdir -p config/agents/my_agent/tools/my_tool/scripts
```

2. **Create tool manifest** (`tool.yml`):

```yaml
kind: Tool
version: "1.0"
name: "my_tool"

description: "Tool description"

executor:
  runtime: "python"
  script: "./scripts/my_tool.py"

parameters:
  input_param:
    type: "string"
    required: true
    description: "Input parameter"

output_schema:
  type: "object"
  properties:
    result:
      type: "string"
```

3. **Create tool script** (`scripts/my_tool.py`):

```python
#!/usr/bin/env python3
import json
import sys

def main():
    # Read parameters from stdin or argv[1]
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = json.loads(sys.stdin.read())
    
    # Your tool logic here
    result = {
        "success": True,
        "result": "Tool output"
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

4. **Make executable and test**:

```bash
chmod +x config/agents/my_agent/tools/my_tool/scripts/my_tool.py

# Add to agent import
import:
  tools:
    - "my_tool"
```

---

## 📂 Project Structure

```
Cortex-Prime-MK1/
├── services/
│   ├── agent-lib/                      # ⭐ Core Runtime (C++)
│   │   ├── agent-bin                   # CLI executable
│   │   ├── agent-server                # HTTP server
│   │   ├── cli.main.cpp                # CLI implementation
│   │   ├── src/                        # Core source
│   │   │   ├── agent/                  # Agent runtime
│   │   │   │   ├── Agent.cpp           # Main agent class
│   │   │   │   ├── ManifestLoader.cpp  # YAML manifest parsing
│   │   │   │   └── ContextManager.cpp  # Context & variables
│   │   │   ├── protocol/               # Streaming protocol
│   │   │   │   ├── StreamingProtocolParser.cpp
│   │   │   │   └── ActionExecutor.cpp  # Tool/agent execution
│   │   │   ├── tools/                  # Tool registry
│   │   │   │   ├── ToolRegistry.cpp
│   │   │   │   └── InternalTools.cpp   # Built-in tools
│   │   │   └── llm/                    # LLM integration
│   │   │       └── LLMGatewayClient.cpp
│   │   ├── inc/                        # Headers
│   │   ├── config/                     # Agent manifests
│   │   │   ├── agents/
│   │   │   │   ├── sage/               # Research advisor
│   │   │   │   │   ├── agent.yml
│   │   │   │   │   ├── system-prompts/
│   │   │   │   │   │   └── sage.md
│   │   │   │   │   └── tools/
│   │   │   │   │       ├── knowledge_retriever/
│   │   │   │   │       │   ├── tool.yml
│   │   │   │   │       │   └── scripts/
│   │   │   │   │       │       └── knowledge_retriever.py
│   │   │   │   │       └── fact_checker/
│   │   │   │   │           ├── tool.yml
│   │   │   │   │           └── scripts/
│   │   │   │   │               └── fact_checker.py
│   │   │   │   └── demurge/            # Creative builder
│   │   │   │       └── agent.yml
│   │   │   └── _archive/               # Old manifests
│   │   ├── Makefile                    # Build system
│   │   └── README.md
│   │
│   ├── llm_gateway/                    # LLM Provider Abstraction
│   │   ├── main.py                     # FastAPI server
│   │   ├── providers/                  # Multi-provider support
│   │   │   ├── google.py               # Gemini
│   │   │   ├── groq.py                 # Groq
│   │   │   └── ollama.py               # Local models
│   │   └── Dockerfile
│   │
│   ├── manifest_ingestion/             # Manifest Parser (Optional)
│   │   ├── main.py
│   │   ├── parsers/
│   │   ├── models/
│   │   ├── registry/
│   │   └── tests/
│   │
│   ├── runtime_executor/               # Sandboxed Execution (Optional)
│   │   ├── main.py
│   │   ├── executors/
│   │   └── tests/
│   │
│   ├── b-line/                         # Web Dashboard (Optional)
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   │
│   └── chat_test/                      # Protocol Tester (Optional)
│       └── chat_test_service.py
│
├── std/                                # Standard Library
│   └── manifests/
│       ├── agents/                     # Shared agent manifests
│       ├── tools/                      # Shared tool manifests
│       ├── relics/                     # Service manifests
│       ├── workflows/                  # Workflow definitions
│       └── monuments/                  # Complete stacks
│
├── examples/                           # Example use cases
│   ├── simple_agent/
│   ├── tool_chaining/
│   └── custom_workflow/
│
├── docs/                               # Documentation
│   ├── STREAMING_PROTOCOL.md
│   ├── MANIFEST_REFERENCE.md
│   ├── ROADMAP.md
│   └── ARCHITECTURE.md
│
├── docker-compose.yml                  # Full stack orchestration
├── Makefile                            # Root-level commands
└── README.md                           # This file
```

### Key Directories

**`services/agent-lib/`** - The core runtime. Completely standalone, no dependencies on other services.

**`services/llm_gateway/`** - Multi-provider LLM access. Used by agent-lib for streaming inference.

**`std/manifests/`** - Standard library of reusable manifests. Agents can import from here.

**`config/agents/`** - Agent-specific manifests. Self-contained with tools, prompts, and configs.

---

## 📚 Documentation

### Core Documentation

- **[services/agent-lib/README.md](services/agent-lib/README.md)** - Agent-lib complete guide
- **[docs/STREAMING_PROTOCOL.md](docs/STREAMING_PROTOCOL.md)** - XML+JSON fusion protocol specification
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Development roadmap and milestones
- **[TOOL_CREATION_GUIDE.md](TOOL_CREATION_GUIDE.md)** - How to create custom tools

### Service Documentation

- **[services/llm_gateway/README.md](services/llm_gateway/README.md)** - LLM provider integration
- **[services/manifest_ingestion/README.md](services/manifest_ingestion/README.md)** - Manifest validation
- **[services/runtime_executor/README.md](services/runtime_executor/README.md)** - Sandboxed execution
- **[services/b-line/README.md](services/b-line/README.md)** - Web dashboard guide

### Examples

- **[examples/simple_agent/](examples/)** - Basic agent setup
- **[config/agents/sage/](services/agent-lib/config/agents/sage/)** - Production agent example
- **[config/agents/demurge/](services/agent-lib/config/agents/demurge/)** - Creative builder example

---

## 🗺️ Roadmap

### Current Status: Foundation Phase

**Agent-lib v1.2** is production-ready for daily use. The framework is evolving to support advanced features.

### ✅ Completed

**Agent-Lib Core:**
- [x] Streaming XML+JSON protocol parser
- [x] Modern manifest loader (YAML)
- [x] Tool execution system (Python/Node/Shell/Docker)
- [x] Internal action system (system_clock, agent_metadata, etc.)
- [x] Context feed management
- [x] Variable expansion ($TIMESTAMP, $AGENT_NAME, etc.)
- [x] Full conversation history (CAG approach)
- [x] CLI binary with interactive commands
- [x] HTTP server (FastAPI integration)
- [x] LLM Gateway integration (streaming inference)
- [x] Production agents (Sage, Demurge)

**Supporting Services:**
- [x] LLM Gateway (multi-provider streaming)
- [x] Manifest Ingestion (validation & hot-reload)
- [x] Runtime Executor (sandboxed execution)
- [x] B-Line Dashboard (web UI)
- [x] Chat Test (protocol testing)

### 🚧 In Progress

**Critical Features:**
- [ ] Sub-agent delegation (streaming passthrough)
- [ ] Non-terminating responses (continue iteration after reply)
- [ ] Relic lifecycle management (health checks, auto-start, monitoring)
- [ ] Context feed expansion (auto-import std library)
- [ ] Action result variable interpolation ($result_key syntax)

**Nice to Have:**
- [ ] Amulet support (reusable config bundles)
- [ ] Workflow engine (multi-step orchestration)
- [ ] Monument deployment (complete stack management)

### 📋 Planned

**Phase 1: Enhanced Capabilities**
- Agent memory persistence (Neo4j/PostgreSQL)
- Advanced error handling with retries
- Confidence scoring & self-assessment
- Expanded tool library (20+ production tools)

**Phase 2: Distributed Systems**
- Multi-agent coordination
- Message bus integration (NATS/RabbitMQ)
- Distributed workflow execution
- Agent-to-agent streaming delegation

**Phase 3: Observability**
- Structured logging with context
- Prometheus metrics & Grafana dashboards
- Performance profiling
- Resource usage tracking

**Phase 4: Self-Modification**
- Agent introspection & reflection
- Automated manifest generation
- Dynamic tool creation
- Meta-learning capabilities

---

## 🎯 Use Cases

### What You Can Build

**Personal AI Assistant** - Daily driver for tasks, research, code generation, and creative work. Load different agents for different contexts.

**Research Platform** - Agents with knowledge retrieval, fact-checking, and synthesis capabilities. Build a personal knowledge graph.

**Code Generation System** - Specialized agents for different languages and frameworks. Sub-agents for linting, testing, documentation.

**Creative Writing Assistant** - Story development, character building, world-building with persistent context across sessions.

**Task Automation** - Workflows that chain multiple agents and tools. From simple scripts to complex multi-step processes.

**Custom Relics** - Build containerized services that agents can interact with. Vector stores, databases, APIs, etc.

---

## 🤝 Contributing

Cortex-Prime MK1 is a personal research project exploring autonomous AI architectures. While external contributions aren't currently accepted, you're welcome to:

- **Fork** the repository for your own experiments
- **Open issues** for bugs or feature suggestions
- **Star** the repo if you find it useful
- **Share** your own agent manifests and tools

---

## 📊 Current Status

**Phase:** Foundation (Production-Ready Core)  
**Agent-Lib Version:** 1.2  
**Active Agents:** 2 (Sage, Demurge)  
**Streaming Protocol:** XML+JSON Fusion  
**Primary Language:** C++ (runtime), Python (services)  
**Daily Driver:** Yes ✅  
**Production Ready:** Agent-lib core ✅  

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🏛️ Philosophy

**"The Great Work Never Ends"**

Cortex-Prime embodies a philosophy of continuous iteration, bold experimentation, and emergent intelligence. We build systems that are:

- **Sovereign** - Run locally, own your data
- **Modular** - Compose complex from simple
- **Transparent** - Open protocols, inspectable behavior
- **Adaptive** - Context-aware, self-improving
- **Unstoppable** - Resilient, fault-tolerant

---

**Built by [PRAETORIAN_CHIMERA](https://github.com/Trafexofive)**  
**Inspired by the daily need for better AI tooling**

---