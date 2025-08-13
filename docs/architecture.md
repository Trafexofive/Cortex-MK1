# Architecture

## The Chimera Ecosystem

The project is architected as a modular, multi-service ecosystem designed for orchestrating autonomous AI agents. This design is a direct implementation of the **Modularity for Emergence** and **Absolute Sovereignty** axioms from the Himothy Covenant.

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

### Core Components

*   **`services/chimera_core` (The Central Nervous System):** The heart of the ecosystem. This Python service is responsible for:
    *   Loading agent and tool definitions from the filesystem (`agents/`, `tools/`, `connectors/`).
    *   Maintaining registries of all available agents and tools.
    *   Executing the core operational loop of an agent: receiving input, assembling prompts, calling the LLM, and dispatching actions to tools.
    *   It is designed to be stateless, with session management handled by the client and long-term memory offloaded to the `chronicle` service.

*   **`services/api_gateway` (The Membrane):** A FastAPI application that provides a single, unified entry point to the ecosystem. It routes incoming requests to the appropriate backend service, primarily the `chimera_core`.

*   **`front` (The Console):** A React/TypeScript frontend that provides a user interface for interacting with the agents and the ecosystem as a whole.

*   **`agents/`, `tools/`, `connectors/` (The Genome):** These directories contain the declarative, version-controlled definitions for all agents, tools, and connectors. This separation of configuration from code allows for rapid development and modification of the system's capabilities.

*   **`services/*` (The Organs):** These are specialized microservices that provide additional capabilities to the ecosystem. They are designed to be modular and independently deployable. Examples include:
    *   `agent_factory` & `tool_factory`: Services for creating new agents and tools, enabling the ecosystem to be self-modifying.
    *   `chronicle`: A service for long-term memory and conversation history.
