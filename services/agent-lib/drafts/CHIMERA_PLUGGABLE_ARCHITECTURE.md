Understood, Master. Adjusting the pluggable tool module structure to co-locate scripts directly within each tool's "module" folder is a refinement that further enhances encapsulation and makes each tool truly "atomic" in its self-containment. This is a strong move towards "Pragmatic Purity" at the tool level.

Let's update the `CHIMERA_PLUGGABLE_ARCHITECTURE.md` to reflect this more granular pluggability.

---

**`CHIMERA_PLUGGABLE_ARCHITECTURE.md` - Design & Integration Protocol**

**Codename: MODULARITY_COVENANT_V1.1** (Revised for Tool-Scoped Scripts)

**Foreword: The Axiom of Self-Contained Power**

This document outlines the architectural principles and integration protocols for creating and utilizing **Pluggable Agent Modules** and **Pluggable Tool Modules** within PRAETORIAN_CHIMERA's Chimera Ecosystem. The core tenet is to foster self-contained, easily shareable, and independently deployable units of capability, aligning with the "Modularity Maximalist" and "Absolute Sovereignty" (over components) Axioms.

This covenant ensures that new functionalities can be forged, tested, and integrated into the ecosystem with minimal friction and maximum clarity. **Version 1.1 revises the Pluggable Tool Module structure to co-locate scripts directly within their respective tool module directories.**

---

## Part I: Pluggable Tool Modules (Revised Structure)

A Pluggable Tool Module is a self-contained directory that provides one or more related, script-based tools. It includes the YAML definition file for these tools and the actual script(s) that implement their functionality, **now with scripts directly inside the module's folder, typically in a `scripts/` subdirectory within it.**

### 1. Directory Structure of a Pluggable Tool Module (Revised)

A Pluggable Tool Module should reside in a common, well-known directory (e.g., `config/pluggable_tool_modules/`). Each module has its own subdirectory:

```
config/pluggable_tool_modules/
└── <module_name>/                # e.g., sqlite_manager, file_system_crud, image_manipulator
    ├── <module_name>.tool.yml    # YAML file defining the tools provided by this module.
    └── scripts/                  # Directory containing the script(s) implementing the tools.
        └── <script_name>.py      # e.g., manage_sqlite_db.py
        └── <another_script>.sh   # Or other script types as needed.
        └── ...
    └── (README.md)               # Optional: A README specific to this tool module
```

*   **`<module_name>/`**: A descriptive name for the module in `kebab-case` (e.g., `sqlite-manager`).
*   **`<module_name>.tool.yml`**: The YAML file containing an array/dictionary of tool definitions.
*   **`scripts/`**: This directory, **now directly within the `<module_name>/` folder**, houses all script implementations required by the tools defined in the adjacent `<module_name>.tool.yml`.
    *   Paths to these scripts within the `<module_name>.tool.yml` file **MUST** be relative to the YAML file itself. For example, if the YAML is at `config/pluggable_tool_modules/sqlite_manager/sqlite_manager.tool.yml`, and the script is at `config/pluggable_tool_modules/sqlite_manager/scripts/manage_sqlite_db.py`, the path in the YAML would be: `path: "./scripts/manage_sqlite_db.py"`.

### 2. Tool Definition (`<module_name>.tool.yml`)

*   **Standard Tool Schema:** (Remains the same: `name`, `description`, `type: "script"`, `runtime`, `path`, `parameters_schema`, `example_usage`).
*   **`path` (Crucial Change):** The `path` attribute to the script **MUST** be relative to the `.tool.yml` file itself. Given the revised structure, this will typically start with `"./scripts/..."`.
    *   **Example:** For `config/pluggable_tool_modules/sqlite_manager/sqlite_manager.tool.yml`, the path to its script would be `path: "./scripts/manage_sqlite_db.py"`.
*   **Tool Naming & Single Script Logic:** (Remains the same) Cohesive tools can still share a single script, with the runtime/executor passing a `script_operation` or `tool_invoked_name` parameter.

### 3. Script Implementation (`scripts/<script_name>.*`)

(All principles regarding Input, Output, Error Handling, Sandboxing & Security, and Dependencies remain the same as in v1.0).

*   **Location:** Scripts are now directly inside the tool module's dedicated `scripts/` subdirectory.

### 4. Integrating Pluggable Tool Modules into an Agent

An agent profile (`<agent_name>.profile.yml`) integrates a Pluggable Tool Module using the `import:` directive. The path to the module's `.tool.yml` file is key.

```yaml
# In agent's profile YAML (e.g., config/agents/specialized-agents/MyDataAgent/my_data_agent.profile.yml)

import:
  tools:
    # Path relative to this agent profile YAML to the specific .tool.yml file
    - "../../../pluggable_tool_modules/sqlite_manager/sqlite_manager.tool.yml"
    - "../../../pluggable_tool_modules/file_system_crud/file_crud.tool.yml"
    # ... other tool imports ...
```

*   The Chimera runtime resolves the path to the specified `.tool.yml` file.
*   When parsing that `.tool.yml`, the runtime then resolves the script `path` (e.g., `"./scripts/script_name.py"`) **relative to the location of that `.tool.yml` file.** This ensures that the scripts are correctly located within their respective tool module directories.

---

## Part II: Pluggable Agent Modules

The structure and principles for Pluggable Agent Modules remain largely the same as defined in v1.0. The key is that an agent *can* package its own truly unique, agent-specific tools and scripts within its own `./tools/` and `./scripts/` subdirectories.

The revised Pluggable Tool Module structure simply makes the *shared, reusable* tool modules more encapsulated.

```
config/agents/
└── <category>/
    └── <AgentNameMKX>/
        ├── README.md
        ├── <agent_name>.profile.yml
        ├── system-prompts/
        │   ├── README.md
        │   └── <prompt_name>.md
        │
        ├── tools/                  # Tools *packaged with and specific to* THIS AGENT.
        │   ├── README.md
        │   └── agent_specific_toolset.yml # Defines tools whose scripts are in ./scripts/
        │
        └── scripts/                # Script implementations for tools in ./tools/agent_specific_toolset.yml
            ├── README.md
            ├── python/
            │   └── my_agent_specific_script.py
            └── ...
        └── ...
```

*   **Agent's Packaged Tools:** If an agent has tools that are *not* general enough to be a shared `pluggable_tool_module`, it defines them in its own `./tools/<agent_specific_tools>.yml`. The scripts for these tools reside in its own `./scripts/` directory. The `path` in this local tool YAML would be relative, e.g., `"../scripts/python/my_agent_specific_script.py"`.
*   **Importing Shared Modules:** The agent *still* imports shared `pluggable_tool_modules` as described in Part I, Section 4.

---

## Part III: General Best Practices for Pluggability (Reinforced)

1.  **Encapsulation:** Each `pluggable_tool_module` is now even more self-contained, bundling its definition and implementation scripts together. This is good.
2.  **Relative Paths are Key:** Strict adherence to correct relative path resolution is critical for the system to locate all components.
    *   Agent Profile -> Tool Module YAML (e.g., `../../../pluggable_tool_modules/module_X/module_X.tool.yml`)
    *   Tool Module YAML -> Its Scripts (e.g., `./scripts/script.py`)
3.  **Minimize External Dependencies for Scripts:** (Remains critical)
4.  **Clear Interfaces (YAML `description` and `parameters_schema`):** (Remains critical)
5.  **Idempotency:** (Remains critical)
6.  **Comprehensive READMEs:** Each module (tool or agent) **MUST** have a root `README.md`. A `pluggable_tool_module` might also benefit from a `README.md` at its root.
7.  **Versioning:** (Remains a future concern for formalization by `ToolMaintenanceAgentMK1`).

---

**Impact of Revision 1.1:**

*   **Enhanced Tool Encapsulation:** Each tool module is now a fully self-sufficient unit. Copying a `pluggable_tool_modules/<module_name>/` directory to another Chimera system (that has the necessary runtime interpreters) should just work.
*   **Simplified Tool Development:** Developers working on a specific tool module have all its components (YAML + scripts) in one isolated place.
*   **No Change to Agent Import Logic:** Agents still import the `.tool.yml` file. The runtime's path resolution logic simply needs to be robust in handling the two levels of relativity (AgentProfile -> ToolYAML, and then ToolYAML -> Script).

This revised Modularity Covenant v1.1, Master, further refines the architecture towards true plug-and-play components. It demands a slightly more disciplined approach to path management within the runtime but yields greater modular purity.
