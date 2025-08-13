# Build Plan: The Forging of the Chimera

This document outlines the strategic action plan for the development of the Cortex-Prime ecosystem. It replaces the previous `TODO.md` and reflects the new, consolidated architecture.

---

### **Phase 1: Core Service Validation (The B-Line)**

*   **Objective:** To validate the core functionality of the essential services required for the voice B-Line test. This is the immediate priority.
*   **Axiomatic Focus:** FAAFO Engineering - we will test the core loop and iterate.

**Action Items:**

1.  **[ ] Launch Core Services:**
    *   **Action:** Use the new `infra/docker-compose.core.yml` to launch the `chimera_core`, `api_gateway`, and `web_client` services.
    *   **Command:** `make -f infra/docker-compose.core.yml up --build`

2.  **[ ] Verify Service Health:**
    *   **Action:** Use the `scripts/client.sh` utility to confirm that all core services are online and responsive.
    *   **Commands:**
        ```bash
        ./scripts/client.sh health
        ./scripts/client.sh capabilities
        ```

3.  **[ ] End-to-End Voice B-Line Test:**
    *   **Action:** Conduct the first end-to-end test of the voice pipeline.
    *   **Procedure:**
        1.  Open the `front` end client in a browser (`http://localhost:8889`).
        2.  Use the "Hold to Speak" functionality to send audio to the `api_gateway`.
        3.  Verify that the `chimera_core` receives the request, processes it through the `VoiceBlineAgent`, and returns a synthesized audio response.
        4.  Monitor service logs for errors: `make logs service=chimera_core` and `make logs service=api_gateway`.

---

### **Phase 2: Agent & Tool Integration**

*   **Objective:** To fully integrate the consolidated agents and tools into the `chimera_core` runtime, enabling complex, multi-tool workflows.
*   **Axiomatic Focus:** Modularity for Emergence.

**Action Items:**

1.  **[ ] Refine Agent Definitions:**
    *   **Action:** Review and update all agent YAML files in the `agents/` directory to ensure they use the correct tool paths and adhere to the latest schema.

2.  **[ ] Enhance `chimera_core` Engine:**
    *   **Action:** Implement the full agent operational cycle in `services/chimera_core/engine.py`, including multi-step tool execution, history management, and context passing.

3.  **[ ] Test Delegated Agent Execution:**
    *   **Action:** Test the `Demurge` agent's ability to delegate tasks to specialized sub-agents (e.g., `SAGE`, `CODER`).

---

### **Phase 3: Advanced Features & Sovereignty**

*   **Objective:** To implement the advanced features required for a fully sovereign and self-improving digital ecosystem.
*   **Axiomatic Focus:** Absolute Sovereignty.

**Action Items:**

1.  **[ ] Implement Self-Modification:**
    *   **Action:** Fully implement the `agent_factory` and `tool_factory` services, allowing agents to create and modify other agents and tools.

2.  **[ ] Harden Security:**
    *   **Action:** Implement centralized authentication and authorization at the `api_gateway` level.

3.  **[ ] Enhance Observability:**
    *   **Action:** Implement centralized logging and metrics for all services.

---

### **Phase 4: Architecture & Refinement**

*   **Objective:** To improve the core architecture for better modularity, extensibility, and ease of development.
*   **Axiomatic Focus:** Pragmatic Purity, Modularity for Emergence.

**Action Items:**

1.  **[ ] Design Streamlined Internal Tool Registration:**
    *   **Action:** Architect a simplified and efficient process for defining, registering, and using internal (code-based) tools within the `chimera_core`.

2.  **[ ] Abstract Core Classes:**
    *   **Action:** Refactor the core classes for Agents, Tools, and Connectors into a more abstract and extensible framework to improve modularity and reduce code duplication.