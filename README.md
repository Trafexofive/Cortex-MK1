# 🚀 Project: Cortex-Prime MK1 (C++ Core)

**"The distance between thought and action, minimized."**

---

### **Abstract**

This repository contains the **Minimum Viable Pantheon** for the Cortex-Prime ecosystem. It represents a fundamental architectural shift from a Python-based prototype to a high-performance, sovereign **C++ Arbiter Core**. This system is the direct implementation of the **Himothy Covenant**, a set of axioms defining a reality for a society of autonomous AI entities.

### **🏛️ Grand Unified Architecture**

The system is architected as a set of containerized services orchestrated by Docker Compose, with the C++ Arbiter at its heart.

*   **`arbiter_core` (C++):** The Kernel of reality. It loads all entity blueprints (`manifests`), links them into a live registry, and manages their entire lifecycle and cognitive processes (the OODA Loop).
*   **`api_gateway` (Python):** The external membrane. A stateless WebSocket proxy that connects the end-user to the Arbiter's stream protocol.
*   **`llm_gateway` (Python):** The sovereign cognitive abstraction layer. It provides a single, unified endpoint for the Arbiter to access multiple LLM providers.
*   **Manifests (`manifests/`):** The declarative "source code" for every sovereign entity (Agents, Tools, Relics, etc.) in the ecosystem.
*   **Implementations (`implementations/`):** The physical source code (e.g., Python scripts) for the entities defined in the manifests.

### **🛠️ The Forge: Getting Started**

#### **1. Prerequisites**
*   Docker & Docker Compose
*   `make`
*   A C++ compiler that supports C++17 (e.g., g++, clang++)
*   CMake (v3.10+)

#### **2. Configuration**
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Cortex-Prime-MK1-CPP

# 2. Create your local environment file
cp .env.template .env
```
**➡️ CRITICAL:** Open and edit the `.env` file. You must provide a valid `GEMINI_API_KEY` for the LLM Gateway to function.

#### **3. Build and Run**
```bash
# This command will build all service images, including compiling the C++ Arbiter.
make setup

# This command will start the entire ecosystem in detached mode.
make up
```

#### **4. Interacting & Monitoring**
*   **Follow logs for all services:** `make logs`
*   **Follow logs for ONLY the C++ Arbiter:** `make logs-arbiter`
*   **Connect a WebSocket client** to `ws://localhost:8080/v1/session` to interact with the `demurge` agent.
*   **Stop and remove all services and volumes:** `make clean`

---

This blueprint is the foundation. The Great Work continues.