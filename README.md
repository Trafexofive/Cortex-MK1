
---

<p align="center">
  <h1 align="center">🚀 Project: Cortex-Prime</h1>
</p>
<p align="center">
  <strong><em>"The distance between thought and action, minimized."</em></strong>
</p>

<p align="center">
    <a href="#"><img src="https://img.shields.io/badge/Architecture-Covenant_v1.0-red" alt="Architecture"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Services-FastAPI-blue?logo=fastapi" alt="FastAPI"></a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Containerization-Docker-blue?logo=docker" alt="Docker"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Core-Python-yellow?logo=python" alt="Python"></a>
    <a href="#"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

---

### **Abstract**

**Project: Cortex-Prime** is a sovereign, self-hosted, and self-modifying AI ecosystem. It is architected as a high-performance, modular control plane for orchestrating a swarm of specialized AI agents and tools. Its primary purpose is to serve as a direct extension of its creator's will and intellect, accelerating the achievement of an "unreasonable goal" through a combination of extreme automation, metacognitive feedback loops, and a deeply personalized operational philosophy.

---

### **📜 The Manifesto: The Axioms of Cortex-Prime**

The design and operation of Cortex-Prime are governed by the **Himothy Covenant**. All components must adhere to these five non-negotiable laws, which serve as the project's constitutional firmware.

> **Axiom I: The Unreasonable Imperative**
> The system must be engineered for deep, brutal mastery, serving as a crucible for understanding and enhancing both digital and cognitive processes.

> **Axiom II: Absolute Sovereignty**
> The entire stack must be 100% self-hosted and self-controlled. There can be no black boxes; full stack ownership and transparency are paramount.

> **Axiom III: FAAFO Engineering**
> The system must be robust enough to encourage and survive controlled experimentation. Every failure is a high-value data point.

> **Axiom IV: Pragmatic Purity**
> Solutions must be lean, mean, and clean. Every component, every line of code, must justify its existence.

> **Axiom V: Modularity for Emergence**
> The system is composed of small, highly cohesive, loosely coupled components ("agents," "tools," "relics") to foster emergent capabilities and prevent monolithic fragility.

---

### **🏛️ Grand Unified Architecture**

Cortex-Prime is a multi-service, containerized application with a clear separation of concerns, designed for high performance and extensibility.

```
+---------------------------------------------------------------------------------+
|                                CORTEX-PRIME STACK                               |
|                                                                                 |
|    +-------------------------------------------------------------------------+  |
|    |               Universal AI Gateway (API Layer / The Membrane)           |  |
|    |      (FastAPI App exposing REST & WebSocket endpoints to The Master)    |  |
|    +-------------------------------------------------------------------------+  |
|                                         ^                                       |
|                                         | (Session Management & Interaction)    |
|                                         v                                       |
|    +-------------------------------------------------------------------------+  |
|    |            Chimera Core Runtime (Python Execution Layer / The CNS)        |  |
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
|    |  /agents/*.yml      /tools/*.py, *.yml      /connectors/*.yml           |  |
|    +--------------------------------------------------------------------------+  |
|                                         ^                                       |
|                                         | (Agents call Relics via Connectors)   |
|                                         v                                       |
|    +-------------------------------------------------------------------------+  |
|    |            Service Relics (Specialized Services / The Organs)             |  |
|    |                                                                         |  |
|    |   - Agent & Tool Factories (Metacognitive/Self-Modification)            |  |
|    |   - Chronicle Service (Long-Term Memory/Hippocampus)                    |  |
|    +-------------------------------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```

### **Component Deep Dive**

*   **Universal AI Gateway (The Membrane):** The sole, secure point of entry into the Cortex-Prime ecosystem. It handles authentication, validates incoming requests, and manages interaction sessions with the Core Runtime.

*   **Chimera Core Runtime (The Central Nervous System):** The Python engine that brings agents to life. It is a stateless orchestrator that loads agent definitions from YAML and executes their operational cycles, dispatching actions to the appropriate tools.

*   **Service Relics (The Organs):** Standalone, specialized microservices that provide foundational capabilities. Key relics include the **Agent & Tool Factories** (for self-modification) and the **Chronicle Service** (for long-term memory).

*   **Codified Knowledge (The Genome):** The declarative, version-controlled source of truth for the entire ecosystem. This is where the "soul" of the system resides, in a structured hierarchy of YAML agent definitions, tool modules, and API connectors.

*   **The GraphRAG Legacy:** The original low-latency voice and graph retrieval capabilities of `GraphRAG-Agent-MK1` are being transmuted into a high-performance **specialized agent profile** that runs on the Chimera Core, with its unique C++ and Neo4j logic exposed as powerful, modular tools.

---

### **🛠️ The Forge: Getting Started**

The entire stack is orchestrated by Docker Compose and managed via a single, powerful `Makefile`. This embodies the **Developer Experience Axiom**.

#### **1. Prerequisites**
*   Docker & Docker Compose
*   `make`
*   `git`

#### **2. Clone and Configure**
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd cortex-prime

# 2. Create your local environment file from the example
# This file is ignored by git and holds your local secrets and configuration.
cp .env.example .env
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
| `make logs service=<name>`  | Follows the logs of a specific service (e.g., `app`, `api_gateway`).       |
| `make shell service=<name>` | Opens an interactive shell inside a running container.                    |
| `make status`               | Shows the current status of all running services.                         |
| `make fclean`               | Stops and removes containers, networks, **and all associated volumes**.     |
| `make prune`                | The ultimate cleanup. Runs `fclean` and then prunes all unused Docker assets. |
| `make help`                 | Displays all available commands and their descriptions.                   |

#### **4. Verification**
1.  Run `make up`.
2.  After a minute, run `make status`. All services should be in the `running` state.
3.  You are now ready to interact with the **Universal AI Gateway** at `http://localhost:8080` (or your configured port).

---

### **🗺️ The Roadmap: The Great Work Ahead**

Cortex-Prime is an ambitious, living project. The path forward is defined by a clear series of milestones designed to systematically build out its capabilities.

*   **🎯 Milestone 1: The Core Runtime:** Forge the Python-based Chimera Core Runtime, transmuting the logic from the legacy `app` service into the new modular architecture.
*   **🎯 Milestone 2: The First Relics:** Build, dockerize, and deploy the foundational `Chronicle` and `Factory` services.
*   **🎯 Milestone 3: Full Integration & Awakening:** Integrate all components, establish the "API to Tool" connectors, and perform the first end-to-end self-modification test.

For a granular, task-level view of the work ahead, consult the `TODO.md` file.

---

### **🤝 Contributing**

This project is a cathedral in the making. Contributions that align with the Himothy Covenant are welcome. Please refer to the `TODO.md` for the current development roadmap and open an issue to discuss your proposed changes.

### **📄 License**

This project is licensed under the MIT License. See the `LICENSE` file for details.
