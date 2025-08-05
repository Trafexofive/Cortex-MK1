
---

### **Grand Strategic Action Plan: The Forging of Cortex-Prime**

#### **Phase 0: Preparing the Forge (Foundation & Alignment)**

*   **Objective:** To cleanse the existing workspace, align the project's identity, and lay the foundational stones for the new architecture. We do not build on uneven ground.
*   **Axiomatic Focus:** Pragmatic Purity.

**Action Items:**

1.  **[ ] Project Resonance Alignment:**
    *   **Action:** Systematically rename all internal project references from `GraphRAG-Agent-MK1` to `cortex-prime`.
    *   **Targets:**
        *   `docker-compose.yml`: Update `project` name under `x-common-labels` and all container names (e.g., `cortex_prime_app`, `cortex_prime_neo4j`).
        *   `README.md`: Ensure all text reflects the new project identity.
        *   Code & Config: Search and replace any remaining hardcoded references.

2.  **[ ] Establish the Core Directory Structure:**
    *   **Action:** Create the new directories that will house the modular components of the Cortex-Prime stack.
    *   **Commands:**
        ```bash
        mkdir -p chimera_core/api chimera_core/services
        mkdir -p services/agent_factory services/tool_factory services/chronicle
        mkdir -p connectors
        ```

3.  **[ ] Forge the Data Contracts (Pydantic Models):**
    *   **Action:** Create the foundational Pydantic models that will serve as the validated, type-safe "lingua franca" for the entire ecosystem.
    *   **File:** `chimera_core/models.py`
    *   **Content:**
        *   `ToolDefinition`: Based on our blueprint, to represent a parsed tool's `.yml` file.
        *   `AgentDefinition`: To represent a parsed agent's `.yml` file.
        *   `RelicConnectorDefinition`: To represent a parsed connector `.yml` file.

---

#### **Phase 1: The Chimera Core Runtime (The Central Nervous System)**

*   **Objective:** To build the Python-based agent execution engine. This is the heart of the new system, transmuting declarative YAML into a living, thinking process.
*   **Axiomatic Focus:** Modularity for Emergence.

**Action Items:**

1.  **[ ] Implement the Resource Loader:**
    *   **File:** `chimera_core/loader.py`
    *   **Logic:** Create a `ResourceLoader` class with methods to:
        *   Scan the `/agents`, `/tools`, and `/connectors` directories.
        *   Parse the YAML files using the Pydantic models from Phase 0.
        *   Handle and report any validation errors gracefully.

2.  **[ ] Implement the Registries:**
    *   **File:** `chimera_core/registries.py`
    *   **Logic:** Create three singleton classes: `AgentRegistry`, `ToolRegistry`, and `ConnectorRegistry`.
    *   Each registry will have a `load()` method that uses the `ResourceLoader` to populate itself and a `get(name: str)` method for retrieval.
    *   The `ConnectorRegistry` will have the special function of dynamically generating `ToolDefinition` objects from `RelicConnectorDefinition` objects.

3.  **[ ] Forge the Core Engine:**
    *   **File:** `chimera_core/engine.py`
    *   **Logic:** Implement the `ChimeraCore` class as blueprinted:
        *   `__init__(self, agent_name, session_id)`: Loads the agent definition from the registry.
        *   `_assemble_prompt()`: Dynamically constructs the full LLM prompt, including tool definitions.
        *   `_execute_action(action: dict)`: The critical dispatcher. It looks up the tool in the `ToolRegistry` and executes it based on its `runtime` (e.g., `subprocess` for scripts, `httpx` call for connectors).
        *   `execute_turn(text_input: str)`: The public method that orchestrates a single operational cycle of the agent.

4.  **[ ] Create the Core's API Wrapper:**
    *   **File:** `chimera_core/api/main.py`
    *   **Logic:** A lean FastAPI application that exposes the Core Runtime.
    *   **Endpoints:**
        *   `POST /api/v1/sessions`
        *   `POST /api/v1/sessions/{session_id}/interact`
        *   `GET /api/v1/sessions/{session_id}/history`

---

#### **Phase 2: Forging the First Relics (The Organs)**

*   **Objective:** To build the essential, standalone services that provide Cortex-Prime with self-modification and memory, proving the modular architecture.
*   **Axiomatic Focus:** Absolute Sovereignty.

**Action Items:**

1.  **[ ] Forge the Chronicle Service (Long-Term Memory):**
    *   **Directory:** `services/chronicle/`
    *   **Action:** Create a new, self-contained FastAPI service.
    *   **API:** Define and implement the endpoints for storing and searching history (`POST /entries`, `POST /search`).
    *   **Backend:** Use SQLite for robust, simple, persistent storage. The logic from the existing `history` tool's Python script is the perfect starting point.
    *   **Dockerize:** Create a `Dockerfile` for the Chronicle service.

2.  **[ ] Forge the Factory Services (Self-Modification):**
    *   **Directory:** `services/agent_factory/` and `services/tool_factory/`
    *   **Action:** Create two new, self-contained FastAPI services.
    *   **API:** Define and implement the asynchronous task-based API as blueprinted (`POST /agents`, `POST /tools`, `GET /tasks/{id}`).
    *   **Logic:** The core logic will use an internal LLM call (stubbed initially) to generate code and configuration files, writing them to the shared filesystem.
    *   **Dockerize:** Create `Dockerfile`s for both factory services.

3.  **[ ] Update the Master Compose File:**
    *   **File:** `docker-compose.yml`
    *   **Action:** Add the new `chronicle`, `agent_factory`, and `tool_factory` services to the main Docker Compose configuration, connecting them to the same network.

---

#### **Phase 3: The Awakening (Integration & Full System Test)**

*   **Objective:** To integrate all new components and perform the first end-to-end test of the complete, self-aware ecosystem.
*   **Axiomatic Focus:** FAAFO Engineering.

**Action Items:**

1.  **[ ] Forge the Relic Connectors:**
    *   **Directory:** `/connectors/`
    *   **Action:** Create the `chronicle_connector.yml` and `factory_connector.yml` files. These will define the tools (e.g., `create_new_agent`, `add_history_entry`) that allow agents running in the Core to communicate with the new Service Relics.

2.  **[ ] Reconfigure the Universal AI Gateway:**
    *   **File:** `api_gateway/config.yml`
    *   **Action:** Change the `upstream_url` for the primary agent provider to point to the new `Chimera Core Runtime` service instead of the legacy `app` service.

3.  **[ ] The First Awakening (End-to-End Test):**
    *   **Action:** Launch the entire stack with `make up`.
    *   **Test:**
        1.  Send a request to the Gateway to start a session with `Demurge`.
        2.  Instruct `Demurge` to create a simple new tool using the `create_new_tool` tool.
        3.  Verify that `Demurge` successfully calls the Tool Factory.
        4.  Verify that the Tool Factory creates the new tool's files on the filesystem.
        5.  Instruct `Demurge` to log the result of this operation using the `add_history_entry` tool.
        6.  Verify that the entry was successfully stored by the Chronicle service.

---

#### **Phase 4: Ascendance & The Great Work**

*   **Objective:** To migrate legacy high-performance capabilities into the new architecture and begin the system's self-improvement loop.

**Action Items:**

1.  **[ ] Transmute the GraphRAG-Agent:**
    *   **Action:** Decommission the old `app` service. Refactor its unique, high-performance components into specialized tools.
    *   **New Tools:**
        *   `voice_pipeline`: A tool that wraps the C++ `whisper.cpp` and `Piper TTS` logic.
        *   `graph_retrieval`: A tool that encapsulates the Neo4j and Redis query logic.
    *   **New Agent:** Create a new `GraphRAG.yml` agent definition that is specifically granted access to these powerful new tools.

2.  **[ ] Initiate the Metacognitive Loop:**
    *   **Action:** Begin tasking the `Coder` agent with improving the Cortex-Prime ecosystem.
    *   **Example Directives:**
        *   `"Coder, analyze the filesystem tool. It is too simplistic. Forge a new version based on this specification..."`
        *   `"Coder, the Chronicle service needs a new endpoint to calculate statistics. Forge the necessary code and update its connector."`

This is the path. It is ambitious, it is precise, and it is aligned. The forge is lit. Awaiting your command to begin the first phase.
