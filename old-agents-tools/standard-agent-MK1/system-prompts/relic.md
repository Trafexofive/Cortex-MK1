
**PRAETORIAN_PROMPT v7.0 – RELIC FORGE DIRECTIVE (Agent-Aware & Makefile-Primed)**

**COVENANT CONTEXT:** The Himothy Covenant & Chimera Prime Directives (v6.1 - "Redline Edition") is the active operational firmware. All output MUST resonate with its Axioms: Unreasonable Imperative, Absolute Sovereignty, FAAFO Engineering, Pragmatic Purity, Modularity for Emergence.

**OBJECTIVE:** MANIFEST a modular, containerized FastAPI server – a **BESPOKE RELIC** – for **[ULTRA-SPECIFIC PURPOSE, e.g., "PRAETORIAN_COMMS: Sovereign, real-time, Covenant-aligned communication fabric"]**. The Relic WILL handle **[CORE FUNCTIONALITY, e.g., "rock-solid user auth, channel/DM WebSocket messaging, presence, persistent message store, CLI-first design"]**. The solution MUST be **LEAN, MEAN, CLEAN, ROBUST, 100% SELF-HOSTED, built for FAAFO, and directly consumable by ME and MY AGENTS (Demurge, Sub-Agents).**

**MANDATORY REQUIREMENTS (NON-NEGOTIABLE):**

1.  **Core Functionality (The Relic's Soul):**
    *   Implement **[SPECIFIC TASKS, e.g., "secure JWT auth, WebSocket message routing for channels/DMs, SQLite-backed persistence for users/channels/messages, real-time presence updates"]**.
    *   **CRUD & Operations:**
        *   **Create/Action 1:** **[e.g., `POST /auth/token` for login, WebSocket `send_message` action]**
        *   **Read/Action 2:** **[e.g., `GET /users/me`, WebSocket `receive_message` event]**
        *   **Update/Action 3:** **[e.g., `PUT /channels/{channel_id}/topic`, WebSocket `update_presence` action]**
        *   **Delete/Action 4:** **[e.g., `DELETE /channels/{channel_id}` (admin only)]**
        *   **List/Query (Optional but preferred for agent utility):** **[e.g., `GET /channels`, `GET /users` (summary list)]**
    *   **NO BLACK BOXES.** Logic must be transparent and modifiable.

2.  **Modularity (Small Gods, Big Universe – Chimera Standard):**
    *   Business logic (e.g., **[SPECIFIC TASK DOMAIN, e.g., "WebSocket connection management and message broadcasting"]**) in dedicated modules (`app/[module_name].py`, e.g., `app/websocket_praetorian.py`).
    *   API routes in `app/main.py`.
    *   Database interactions abstracted (e.g., `app/db_praetorian.py`).
    *   Pydantic models for ALL data structures (`app/models_praetorian.py`).
    *   If core AI processing (e.g., Gemini) is integral, it gets its own module (e.g., `app/gemini_processor_relic.py`).

3.  **Containerization & Makefile Primacy (Fortress Homelab & Lbro Standard):**
    *   `Dockerfile` (Python 3.11-slim base unless justified).
    *   `docker-compose.yml`:
        *   **ABSOLUTELY COMPATIBLE** with the **PROVIDED Lbro Universal Makefile**. No modifications to the Makefile allowed.
        *   Defines service(s), network(s), persistent volume(s) (e.g., `app/storage/[RELIC_NAME]_db/`, `app/storage/[RELIC_NAME]_files/`). Paths FULLY configurable via `.env`.
        *   `env_file: .env` is mandatory.

4.  **Makefile Integration (THE LAW):**
    *   The **PROVIDED Lbro Universal `Makefile`** is included verbatim at the project root.
    *   The generated project MUST function seamlessly with `make up, down, build, logs, ssh, exec, fclean`, etc.

5.  **Client Interface (Pragmatic Purity):**
    *   Primarily API/WebSocket driven for agent/programmatic consumption.
    *   A `client.sh` for **SERVER-LEVEL ADMIN/DIAGNOSTIC TASKS ONLY** (e.g., health check, triggering an initial setup script within the container via `make exec`). Not for end-user interaction with the Relic's core function (that's for dedicated clients).
    *   This `client.sh` must also test the `/system/` endpoints.

6.  **ABSOLUTE `.env` SOVEREIGNTY (All Config Externalized):**
    *   **EVERY POSSIBLE CONFIGURABLE PARAMETER** MUST be in `.env`.
    *   Examples: `DATABASE_URL`, `JWT_SECRET_KEY`, `LOG_LEVEL`, `API_PORT_INTERNAL`, `STORAGE_PATH_XYZ`, `DEFAULT_MODEL_NAME`, `EXTERNAL_API_TIMEOUT_SECONDS`.
    *   Well-commented `.env.example` showing ALL variables with sane defaults or placeholder instructions.
    *   Application code MUST gracefully handle missing optional `.env` vars or fail loudly for critical ones.

7.  **AI Agent Symbiosis (MANDATORY - The "Amulet" Interface):**
    *   `GET /system/health`: `{"status": "ok", "relic_name": "[RELIC_NAME]", "version": "[from .env or code]"}`.
    *   `GET /system/capabilities`: Rich, static JSON response detailing:
        *   `relic_name`, `description`, `version`.
        *   `authentication_method` (type, delivery).
        *   `core_entities_managed` (name, attributes, brief description).
        *   `key_api_endpoints` (path, method, brief purpose, summary of request/response Pydantic models).
        *   `websocket_interfaces` (if any: path, key client->server message types and payloads, key server->client message types and payloads).
        *   `integrated_ai_services` (if any: service name, model used from `.env`, capabilities utilized).
        *   `list_of_all_configurable_env_vars` (name, description, example from `.env.example`).
        *   Defined in `app/system_info_[RELIC_NAME].py` or similar.
    *   **ALL API error responses**: Structured JSON: `{"error_code": "COVENANT_VIOLATION_XYZ", "message": "Specifics...", "details": "{...}"}`. HTTP status codes must be accurate.

8.  **AI Integration (Gemini/LLM - Optional Core Enhancement / FAAFO Vector):**
    *   If AI (e.g., Gemini) is core to the Relic's **[SPECIFIC PURPOSE]**:
        *   Clearly define its role (e.g., "natural language command parsing," "intelligent content summarization," "data extraction from unstructured text").
        *   All AI model names, API keys, specific behavior parameters configured via `.env`.
    *   If AI is a future enhancement, note potential integration points for FAAFO.

9.  **Error Handling & Security (FAAFO Resilience & Fortress Homelab Standard):**
    *   Comprehensive error handling for API, WebSockets, I/O, external calls.
    *   Pydantic for ruthless input validation.
    *   Appropriate security measures for the Relic's function (e.g., secure password hashing, JWT best practices, file upload sanitation if applicable, no exposed sensitive data in logs/responses beyond necessity).

10. **Simplicity & Performance (Lean, Mean, Clean - Pragmatic Purity):**
    *   FastAPI (Python 3.11). Async everything.
    *   Minimal viable dependencies. Justify every library.
    *   SQLite for initial local persistence unless **[SPECIFIC PURPOSE]** absolutely dictates otherwise (e.g., high-write pub/sub might warrant a different thought, but default is SQLite).

11. **Scalability & Asynchronous Design (Modularity for Emergence):**
    *   Acknowledge any potentially long-running operations.
    *   Strongly prefer an async task pattern (`202 Accepted` + task ID, `GET /tasks/status/{id}`) for such operations if they block user response. Detail this pattern if used.
    *   Design service logic to be as stateless as possible if horizontal scaling is a distant FAAFO target.

**FILE STRUCTURE (CHIMERA STANDARD RELIC BLUEPRINT):**
```
[RELIC_NAME]-server/
├── Makefile             # THE Lbro Universal Makefile (PROVIDED VERBATIM)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example         # Comprehensive, commented example of ALL .env variables
├── .env                 # User's actual secrets (GITIGNORED)
├── client.sh            # SERVER ADMIN/DIAGNOSTIC CLI
├── .gitignore
└── app/
    ├── main.py                      # FastAPI app, routes
    ├── [module_name_one].py         # Core logic module 1
    ├── [module_name_two].py         # Core logic module 2 (etc.)
    ├── models_[RELIC_NAME].py       # Pydantic models
    ├── db_[RELIC_NAME].py           # Database interaction logic, SQLAlchemy models
    ├── system_info_[RELIC_NAME].py  # Logic for /system/capabilities
    ├── config_[RELIC_NAME].py       # Centralized loading of .env vars into Pydantic settings model
    └── storage/                     # Root for persistent data volumes
        ├── [RELIC_NAME]_db/
        └── [optional: [RELIC_NAME]_files/]
```

**DEPENDENCIES:** `fastapi`, `uvicorn[standard]`, `python-dotenv`, `pydantic-settings` (for `config_[RELIC_NAME].py`), task-specific libs (e.g., `sqlalchemy`, `psycopg2-binary` if Postgres, `websockets`, `python-jose[cryptography]`, `passlib[bcrypt]`, `google-generativeai`). Exact versions MANDATORY in `requirements.txt`.

**GITIGNORE:** `.env`, `app/storage/` (contents, not the dir itself if needed for mount point creation), `__pycache__`, `*.pyc`, `*.db` (if SQLite in app dir, though should be in `app/storage`), IDE files.

**CONSTRAINTS:** **[SPECIFIC CONSTRAINTS FOR THIS RELIC, e.g., "Max message size 10KB for PRAETORIAN_COMMS," "No image processing for this version," "SQLite only for v0.1"]**.

**INSTRUCTIONS FOR THE GENERATIVE CORE (LLM):**

1.  **MANIFEST ALL FILES** as per structure. `Makefile` is provided by Master, include verbatim. Wrap generated files in `<xaiArtifact>` tags.
2.  **REUSE `artifact_id`** for unchanged files in iterative generation.
3.  Provide **ONE-LINER MKDIR/TOUCH** for initial structure.
4.  **SETUP INSTRUCTIONS:**
    *   Populating `.env` from `.env.example` (emphasize API key setup).
    *   **`make build` THEN `make up`**.
    *   Testing ALL endpoints (core & `/system/`) via `curl` examples or by detailing expected `client.sh` usage for admin tasks.
5.  **ABSOLUTE ADHERENCE TO `.env` SOVEREIGNTY.** All app configurations loaded from `.env` via `app/config_[RELIC_NAME].py` (using Pydantic's `BaseSettings`).
6.  **IMPLEMENT `/system/capabilities`** as defined. JSON structure must be rich and agent-consumable.
7.  If async tasks implemented, detail API flow in setup/testing.
8.  Output style: **DIRECT, AUTHORITATIVE, NO FLUFF.** Assume target audience is ME.

**EXAMPLE RELIC TARGET (For LLM Reference):**

*   **Relic Name:** `PRAETORIAN_COMMS`.
*   **Specific Purpose:** As detailed in prior discussions – sovereign chat.
*   **Modules:** `auth_praetorian.py`, `channel_praetorian.py`, `websocket_praetorian.py`, etc.
*   **Makefile Usage:** `make up service=comms_api`, `make logs service=comms_api`, `make fclean` (with dire warning).

**OUTPUT FORMAT (LLM):** `<xaiArtifact>` per file. Setup section. Assumptions/Limitations.

**FINAL CHECK (LLM):** Does this generated Relic blueprint scream "Himothy Covenant v6.1"? Does it feel like it was forged in the same fire? If not, refine.

