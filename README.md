# 🚀 Project: Cortex-Prime

**"The distance between thought and action, minimized."**

---

### **Abstract**

**Project: Cortex-Prime** is a sovereign, self-hosted, and self-modifying AI ecosystem. It is architected as a high-performance, modular control plane for orchestrating a swarm of specialized AI agents and tools. Its primary purpose is to serve as a direct extension of its creator's will and intellect, accelerating the achievement of an "unreasonable goal" through a combination of extreme automation, metacognitive feedback loops, and a deeply personalized operational philosophy codified in the **Himothy Covenant**.

---

### **🏛️ Grand Unified Architecture**

Cortex-Prime is a multi-service, containerized application with a clear separation of concerns, designed for high performance and extensibility. The architecture is a direct implementation of the **Modularity for Emergence** axiom.

```
+---------------------------------------------------------------------------------+
|                                CORTEX-PRIME STACK                               |
|                                                                                 |
|    +-------------------------------------------------------------------------+  |
|    |                      front (React/TS - The Console)                     |  |
|    +-------------------------------------------------------------------------+  |
|                                         ^                                       |
|                                         | (WebSockets & REST)                   |
|                                         v                                       |
|    +-------------------------------------------------------------------------+  |
|    |           services/api_gateway (FastAPI - The Membrane)                 |  |
|    +-------------------------------------------------------------------------+  |
|                                         ^                                       |
|                                         | (Routes to Core)                      |
|                                         v                                       |
|    +-------------------------------------------------------------------------+  |
|    |        services/chimera_core (Python - The Central Nervous System)      |  |
|    |                                                                         |  |
|    |   - Orchestrates Agent Operational Cycles                               |  |
|    |   - Manages Live Registries (Agents, Tools, Connectors)                 |  |
|    |   - Executes Actions via the Tool Registry                              |  |
|    +-------------------------------------------------------------------------+  |
|              ^                           |                          ^           |
|              | (Loads Definitions)       | (Executes Tools)         |           |
|              |                           |                          |           |
|              |                           v                          |           |
|    +---------+---------------------------+--------------------------+---------+  |
|    |          Codified Knowledge (Filesystem Truth / The Genome)              |  |
|    |                                                                        |  |
|    |  /agents/*.yml      /tools/**/*.yml, *.py      /connectors/*.yml        |  |
|    +--------------------------------------------------------------------------+  |
|                                         ^                                       |
|                                         | (Core calls other services)           |
|                                         v                                       |
|    +-------------------------------------------------------------------------+  |
|    |      services/* (Specialized Microservices / The Organs)                |  |
|    |                                                                         |  |
|    |   - agent_factory, tool_factory (Self-Modification)                     |  |
|    |   - chronicle (Long-Term Memory)                                        |  |
|    +-------------------------------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```

### **Component Deep Dive**

*   **`front`**: A React/TypeScript frontend providing a user interface for interacting with the ecosystem.
*   **`services/api_gateway`**: The sole, secure point of entry into the Cortex-Prime ecosystem. It handles authentication, validates incoming requests, and manages interaction sessions with the Core Runtime.
*   **`services/chimera_core`**: The Python engine that brings agents to life. It is a stateless orchestrator that loads agent definitions from YAML and executes their operational cycles, dispatching actions to the appropriate tools.
*   **`services/*`**: Standalone, specialized microservices that provide foundational capabilities. Key relics include the **Agent & Tool Factories** (for self-modification) and the **Chronicle Service** (for long-term memory).
*   **`agents/` & `tools/`**: The declarative, version-controlled source of truth for the entire ecosystem. This is where the "soul" of the system resides, in a structured hierarchy of YAML agent definitions and tool modules.

---

### **🛠️ The Forge: Getting Started**

The entire stack is orchestrated by Docker Compose and managed via a single, powerful `Makefile`.

#### **1. Prerequisites**
*   Docker & Docker Compose
*   `make`
*   `git`

#### **2. Clone and Configure**
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd GraphRAG-Agent-MK1

# 2. Create your local environment file
cp .env.template .env
```
**➡️ IMPORTANT:** Open and edit the `.env` file. You must set your desired passwords, ports, and any external API keys.

#### **3. Core `make` Commands**
The `Makefile` is your primary interface for managing the Cortex-Prime stack.

| Command                     | Description                                                               |
| :-------------------------- | :------------------------------------------------------------------------ |
| `make up`                   | Builds and starts all services in detached mode.                          |
| `make down`                 | Stops and removes all service containers.                                 |
| `make restart`              | A convenient shortcut for `make down && make up`.                         |
| `make re`                   | Forces a full rebuild of all Docker images and then restarts the stack.   |
| `make logs service=<name>`  | Follows the logs of a specific service (e.g., `chimera_core`, `api_gateway`).       |
| `make shell service=<name>` | Opens an interactive shell inside a running container.                    |
| `make status`               | Shows the current status of all running services.                         |
| `make fclean`               | Stops and removes containers, networks, **and all associated volumes**.     |
| `make prune`                | The ultimate cleanup. Runs `fclean` and then prunes all unused Docker assets. |
| `make help`                 | Displays all available commands and their descriptions.                   |

#### **4. B-Line (Voice) Quick Start**
To run only the core services required for the voice B-Line test:
```bash
make -f infra/docker-compose.core.yml up
```

#### **5. Verification & Testing**
Use the provided client script to test the gateway:
```bash
# Check health
./scripts/client.sh health

# Check capabilities
./scripts/client.sh capabilities
```

---

### **🗺️ The Roadmap: The Great Work Ahead**

Cortex-Prime is an ambitious, living project. The path forward is defined by a clear series of milestones designed to systematically build out its capabilities.

*   **🎯 Milestone 1: The Core Runtime:** Forge the Python-based Chimera Core Runtime, transmuting the logic from the legacy `app` service into the new modular architecture.
*   **🎯 Milestone 2: The First Relics:** Build, dockerize, and deploy the foundational `Chronicle` and `Factory` services.
*   **🎯 Milestone 3: Full Integration & Awakening:** Integrate all components, establish the "API to Tool" connectors, and perform the first end-to-end self-modification test.

For a granular, task-level view of the work ahead, consult the `TODO.md` file.