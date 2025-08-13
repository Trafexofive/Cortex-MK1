# The Chimera Canvas: Vision & Blueprint

This document is the definitive, living design specification for the Chimera Ecosystem. It fuses the core philosophy and vision with the concrete technical blueprints that guide its construction. This is our shared canvas.

---

## Part I: The Vision & Philosophy (The "Why")

*(This section is based on the analysis of the ancestor project, `agent-lib`, and represents the guiding philosophy for the current ecosystem.)*

### **An In-Depth Analysis of the Chimera Ecosystem: Forging a Digital Sovereign**

This project is the physical manifestation of a digital philosophy. It represents the foundational layer of the **Chimera Ecosystem**, a sovereign, self-hosted, and continuously evolving environment designed for a fleet of autonomous AI agents. The driving force behind every line of code, every architectural choice, and every system prompt is a codified set of principles known as **The Himothy Covenant**.

The ultimate vision is breathtaking in its ambition: to create a digital organism that is not just a tool for its creator (referred to as "The Master" or "PRAETORIAN_CHIMERA"), but a mirror for self-discovery and a crucible for achieving an "unreasonable goal to get unreasonably good."

### **Pillar I: The Covenant as Architectural Blueprint**

The design of the Chimera Ecosystem is a direct translation of the Himothy Covenant's five axioms into engineering principles.

*   **Axiom I & II (Unreasonable Imperative & Absolute Sovereignty):** These axioms dictate a technological stack that ensures ultimate control, maximum performance, and a "no black boxes" approach.
*   **Axiom III (FAAFO Engineering):** The "Fuck Around and Find Out" principle is formalized in the project's structure, with specialized agents and testing grounds to facilitate and automate rigorous, controlled experimentation.
*   **Axiom IV (Pragmatic Purity):** This axiom champions "No Bullshit Engineering." The architecture is clean, logical, and avoids unnecessary complexity. The strict JSON schema that agents must adhere to is the ultimate enforcement of this purity.
*   **Axiom V (Modularity for Emergence):** The entire ecosystem is composed of hyper-modular, self-contained units (Agents, Tools, Relics) designed to be pluggable and composable, creating the potential for emergent behaviors.

### **Pillar II: The Anatomy of a Chimera Agent - A Hybrid Organism**

Each agent is a hybrid entity, blending high-performance compiled code with the flexibility of declarative configuration and scripted tools.

*   **The Brainstem:** The core reasoning loop, tool registry, and LLM API interactions.
*   **The YAML DNA:** Declarative files that define an agent's identity, personality, and capabilities by importing specific tool modules.
*   **The Appendages (Tools & Relics):** Independent scripts that allow the agent to interact with its environment, providing a powerful separation of concerns.

### **Pillar III: The Society of Agents - An Orchestrated Hierarchy**

The ecosystem is a structured society with a clear chain of command, enabling complex task decomposition and delegation.

*   **The Orchestrator ("Demurge"):** The master agent and central planner that interprets high-level intent and breaks it down into concrete sub-tasks.
*   **The Specialists (e.g., `SAGE`, `GATE`, `CODER`):** Worker agents, each a master of its domain (memory, testing, coding).
*   **Inter-Agent Communication:** A concrete mechanism for delegation, allowing for powerful, recursive workflows.

### **Pillar IV: The Arsenal of Sovereignty - A Maturing Tooling Ecosystem**

The tools are the agent's connection to reality, forming a sophisticated perceptual and cognitive apparatus.

*   **Sensing & Memory Tools (`web_search`, `history`, `artifacts`):** Allow the agent to perceive the outside world and provide it with persistent memory.
*   **Manipulation & Action Tools (`filesystem_unrestricted`, `bash`):** The agent's hands, providing a direct and powerful interface to the underlying operating system.
*   **Evolutionary Tools:** Create a metaprogrammatic loop, giving the system the potential for self-directed evolution.

---

## Part II: The Technical Blueprint (The "How")

### Schema v1.0: Synchronous Baseline

This is the current operational schema. It's robust for synchronous, single-turn actions.

```json
{
  "status": "string (Enum: SUCCESS | EXECUTING | ERROR | ...)",
  "thoughts": [
    {
      "type": "string (Enum: PLAN | OBSERVATION | ...)",
      "content": "string"
    }
  ],
  "actions": [
    {
      "action": "string",
      "type": "string (Enum: tool | script | internal)",
      "params": "object",
      "execution": "string (Enum: SYNC | ASYNC | ...)",
      "confidence": "float",
      "warnings": ["string"]
    }
  ],
  "stop": "boolean",
  "response": "string | null"
}
```

### Schema v2.0 (Prototype): Asynchronous Operations & Context Management

This prototype introduces concepts for handling long-running (asynchronous) tool calls and explicit context passing.

#### Key Additions:

1.  **`task_id` in Action:** When an `ASYNC` action is dispatched, the system immediately returns a `task_id`.
2.  **New `status`:** A `TASK_STARTED` status to indicate that an async process has been initiated.
3.  **`context` Block:** A new top-level block to define the context for the current operation.

#### Example v2.0 Prototype: Kicking off an Async Task

**Scenario:** The user asks the agent to start a long-running code compilation.

```json
{
  "status": "TASK_STARTED",
  "context": {
    "knowledge_relics": ["relic_id_project_docs_v4"],
    "security_level": "user"
  },
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The Master has requested a compilation. This is a long-running task. I will dispatch it as an asynchronous action using the 'build_tool' and immediately return a task ID so the Master is not blocked."
    },
    {
      "type": "DECISION",
      "content": "Using 'build_tool' with 'target: //main:app' as an ASYNC action."
    }
  ],
  "actions": [
    {
      "action": "build_tool",
      "type": "tool",
      "params": {
        "target": "//main:app",
        "config": "release"
      },
      "execution": "ASYNC"
    }
  ],
  "stop": true,
  "response": "Compilation task started. You can check the status using the task ID: a7b3c9d1-e4f6-4g8h-9i1j-k2l3m4n5o6p7"
}
```

#### Example v2.0 Prototype: Context Management

**Scenario:** The user wants to summarize a document, but the agent needs to know which knowledge "relic" to use.

```json
{
  "status": "EXECUTING",
  "context": {
    "knowledge_relics": ["relic_id_project_docs_v2"],
    "security_level": "user"
  },
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The user wants a summary. I will use the 'summarizer' tool, but I will explicitly scope its context to the 'project_docs_v2' knowledge relic to ensure it doesn't pull from irrelevant sources."
    }
  ],
  "actions": [
    {
      "action": "summarizer_tool",
      "type": "tool",
      "params": {
        "query": "Provide a summary of the new architecture.",
        "target_document": "architecture.md"
      }
    }
  ],
  "stop": false,
  "response": null
}
```
