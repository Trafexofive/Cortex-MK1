
---
<p align="center">
  <h1 align="center">🚀 Project: Cortex MK1</h1>
</p>
<p align="center">
  <strong><em>"The distance between thought and action, minimized."</em></strong>
</p>

<p align="center">
    <a href="https://github.com/prettier/prettier">
    <img alt="code style: prettier" src="https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI-blue?logo=fastapi" alt="FastAPI"></a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Container-Docker-blue?logo=docker" alt="Docker"></a>
    <a href="https://neo4j.com/"><img src="https://img.shields.io/badge/Database-Neo4j-blue?logo=neo4j" alt="Neo4j"></a>
    <a href="https://github.com/ggerganov/whisper.cpp"><img src="https://img.shields.io/badge/ASR-whisper.cpp-green" alt="whisper.cpp"></a>
    <a href="#"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

---

This repository contains **Project: Cortex MK1**, a production-grade, high-performance AI control plane designed to orchestrate any AI service, model, or workflow. It provides a single, standardized, and extensible API for your entire AI ecosystem.

Cortex is built on two primary pillars:
1.  The **Universal AI Gateway**: A central routing and transformation layer that unifies access to any AI provider.
2.  The **GraphRAG-Agent-MK1**: Its premier backend service; a voice-first conversational agent with a sub-200ms voice-to-voice latency, built on a streaming, predictive GraphRAG engine.

## 📜 The Manifesto: The Axioms of Cortex

Cortex is not merely a collection of code; it is an opinionated implementation of a philosophy. Our development is guided by a set of core axioms that dictate every architectural decision.

> **The Efficiency Axiom: *Every interaction should minimize the distance between thought and action.***
> Latency is the enemy of flow. Cortex is architected from the ground up for extreme low-latency. From the streaming-first pipeline to the in-memory graph queries and C++-based voice models, every component is selected and optimized to ensure that the agent's response feels instantaneous, creating a seamless extension of the user's own cognitive process.

> **The Compositional Design Axiom: *Complex systems should be buildable from simple, interchangeable components.***
> Monoliths are rigid and fragile. Cortex is a microservices-based system of simple, well-defined components (`api_gateway`, `app`, `neo4j`, `redis`), each with a clear responsibility. This approach enables scalability, fault tolerance, and, most importantly, extensibility. New capabilities are added by composing new components, not by complicating existing ones.

> **The Cognitive Offloading Axiom: *Systems should carry the burden of remembering so users can focus on creating.***
> The human mind is for creation, not for storage. The GraphRAG engine, with its Neo4j knowledge graph and Redis cache, acts as a perfect, externalized memory. The *predictive* nature of the RAG engine takes this a step further, anticipating information needs before they are consciously articulated, making relevant knowledge instantly available.

> **The Technical Integrity Axiom: *The quality of what's beneath the surface determines long-term success.***
> We do not take shortcuts. The architecture is clean, with a clear separation of concerns. The code is organized and adheres to modern best practices. We use battle-tested, production-grade technologies like FastAPI, Docker, and Neo4j. There are no black boxes; every component is chosen for its performance, reliability, and transparency.

> **The Developer Experience Axiom: *A developer's flow state is as sacred as a user's.***
> A powerful system that is difficult to use is a failed system. The entire project is managed by a single, comprehensive `Makefile`. The Docker-centric workflow guarantees a reproducible environment. Configuration is externalized. The goal is to enable a new developer to go from `git clone` to a fully running, debuggable stack in under five minutes.

## 🎯 Use Cases & Applications of Cortex

The Cortex platform is a powerful foundation for a new generation of applications:

*   **Real-Time Customer Support Agents**: Build voice-driven support agents that can access vast knowledge bases (product manuals, past tickets) in real-time to provide instant, accurate answers.
*   **Hyper-Intelligent Personal Assistants**: Create personal AIs that have a deep, graph-based understanding of your personal and professional life, capable of managing schedules, answering complex queries, and even anticipating your needs.
*   **Interactive Data Analysis & Exploration**: Use voice to have a conversation with your data. Connect the GraphRAG engine to your enterprise data warehouse and allow users to explore complex datasets through natural language queries.
*   **On-Demand Expertise for Professionals**: Imagine a doctor conversing with an agent that has instant access to the entire body of medical literature, or a lawyer querying an agent with perfect knowledge of case law.
*   **Immersive Gaming & Entertainment**: Create NPCs (Non-Player Characters) that have persistent memory, deep knowledge of the game world's lore, and the ability to have truly dynamic, unscripted conversations with players.

---

## ✨ Cortex: Core Features

| Universal AI Gateway                                                                                                                                                                                                                                                                                                                                    | GraphRAG-Agent-MK1 (Backend)                                                                                                                                                                                                                                                                                                                                                                                                                   |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Unified API**: A single `/v1/inference` endpoint for all AI interactions, supporting both REST (`POST`) and real-time streaming (`WebSocket`).                                                                                                                                                                                                           | **<200ms Voice-to-Voice Latency**: A fully streaming pipeline for transcription, graph retrieval, LLM generation, and speech synthesis enables truly natural conversation.                                                                                                                                                                                                                                                                                            |
| **Pluggable Provider Architecture**: A `config.yml`-driven system for seamlessly integrating any AI service—OpenAI, Anthropic, local models via Ollama, or your own custom services.                                                                                                                                                                     | **Predictive Graph RAG Engine**: Anticipates follow-up questions and pre-fetches context from the Neo4j knowledge graph into a Redis cache *before* you even ask.                                                                                                                                                                                                                                                                                               |
| **Automated Transformation Layer**: Automatically transforms the standardized `InferenceRequest` and `InferenceResponse` models to and from provider-specific formats, eliminating boilerplate code.                                                                                                                                                         | **High-Performance Voice Tech**: Uses `whisper.cpp` for ultra-fast, low-footprint transcription and `Piper TTS` for clear, natural speech synthesis with minimal time-to-first-sound.                                                                                                                                                                                                                                                                          |
| **Centralized Control Plane**: Provides the ideal point to implement cross-cutting concerns like authentication, rate limiting, centralized logging, and semantic caching. (See Roadmap).                                                                                                                                                                  | **Dynamic Knowledge Ingestion**: A live `/knowledge/upload` endpoint allows for adding documents to the agent's knowledge graph on the fly.                                                                                                                                                                                                                                                                                                                        |
| **Containerized & Production-Ready**: Built with FastAPI and fully containerized with Docker and Docker Compose, including health checks and restart policies for robust, scalable deployments. A `docker-compose.prod.yml` and Kubernetes manifests are also provided. | **Multi-modal and Multi-lingual**: Distinct WebSocket endpoints for voice (`/voice/stream`) and text-based (`/agent/stream`) interaction. Designed for multilingual support from the ground up, with initial tests for English and Spanish. |

---

## 🏛️ Cortex: System Architecture

The system is architected as a set of cooperating microservices, orchestrated by Docker Compose.

<p align="center">
  <strong>High-Level Service Architecture</strong><br>
  <img src="https://i.imgur.com/g8e1z6Z.png" alt="Architecture Diagram" width="800"/>
</p>

1.  **`api_gateway`**: The public-facing entry point. A lean FastAPI service responsible for:
    *   Exposing the standardized `/v1/inference` API.
    *   Reading the `config.yml` to know about available backends.
    *   Performing request transformation.
    *   Routing traffic to the appropriate internal service.
    *   *Future*: Handling centralized authentication, rate limiting, and caching.

2.  **`app`**: The core application logic for the GraphRAG Agent. This is where the magic happens. It contains several key internal components:
    *   **API Layer (`app/api`)**: Defines the WebSocket endpoints (`/agent/stream`, `/voice/stream`) and REST endpoints (`/knowledge/upload`).
    *   **Service Layer (`app/services`)**: Contains the business logic, like the `LiveAgentService` which orchestrates the interaction between the different components.
    *   **Core Logic (`app/core`)**: Contains the high-performance engines:
        *   `VoicePipeline`: Manages the real-time interaction with `whisper.cpp` and `Piper TTS`.
        *   `GraphRAGEngine`: Executes the RAG logic, interfacing with Neo4j and Redis.
        *   `Neo4jClient` & `RedisClient`: Low-level clients for database interaction.

    <p align="center">
      <strong>Internal `app` Service Data Flow</strong>
    </p>
    <pre align="center">
    Client Audio Stream --&gt; [WebSocket]
             |
             v
    [VoicePipeline: Transcribe with whisper.cpp] --&gt; Transcript
             |
             +----------------------------------+
             |                                  |
             v                                  v
    [GraphRAGEngine: Retrieve]         [GraphRAGEngine: Predict & Pre-cache]
    [Neo4j & Redis]                           [Neo4j & Redis]
             |
             v
    [LLMService: Generate Response] --&gt; Text Stream
             |
             v
    [VoicePipeline: Synthesize with Piper TTS] --&gt; Agent Audio Stream
             |
             v
    [WebSocket] --&gt; Client
    </pre>

3.  **`neo4j`**: The knowledge graph database.
    *   **Data Model**: We use a flexible graph model of `(Node)`s representing entities (e.g., people, documents, concepts) and `[RELATIONSHIP]`s representing the connections between them. This allows for complex, multi-hop queries that are far more powerful than traditional text search.
    *   **Role**: Provides the deep, persistent memory for the RAG engine.

4.  **`redis`**: The in-memory caching layer.
    *   **Caching Strategy**: We use a time-to-live (TTL) cache for RAG query results. The key is a hash of the query string and retrieval parameters. The predictive pre-caching mechanism ensures this cache is "warm" with relevant information before it's even requested.
    *   **Role**: Drastically reduces latency for repeated or predicted queries, ensuring sub-50ms retrieval times in most conversational scenarios.

---

## ⚡ Performance: The Sub-200ms Latency Budget

Achieving real-time interaction requires a strict "latency budget." Our target of <200ms is broken down across the pipeline:

| Pipeline Stage                   | Component             | Latency Target | How We Achieve It                                                                                              |
| :------------------------------- | :-------------------- | :------------- | :------------------------------------------------------------------------------------------------------------- |
| **Voice Activity Detection (VAD)** | `webrtcvad`           | < 30ms         | Highly efficient algorithm for detecting speech onset.                                                         |
| **Speech-to-Text (Transcription)** | `whisper.cpp`         | < 100ms        | Streaming transcription on small audio chunks using a highly optimized C++ backend.                            |
| **RAG Retrieval**                | `GraphRAGEngine`      | < 50ms         | **Predictive Caching** in Redis avoids expensive graph queries. Parallel execution of queries.                 |
| **LLM Time-to-First-Token**      | `LLMService`          | *Varies*       | This is provider-dependent, but by using streaming LLMs, we don't wait for the full response.                  |
| **Text-to-Speech (Synthesis)**   | `Piper TTS`           | < 50ms         | Extremely fast, non-deep-learning-based TTS engine that produces the first chunk of audio almost instantly.    |
| **Total Voice-to-Voice Latency** | **End-to-End**        | **< 200ms**    | The sum of the above, demonstrating the feasibility of natural, real-time voice interaction.                   |

This budget can be benchmarked using the provided script:
```bash
make test
```

---

## 🛠️ Developer Onboarding: From Zero to Running Stack

This guide provides a complete walkthrough for setting up your development environment.

### Step 1: Prerequisites

Ensure you have the following tools installed on your system:
*   [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
*   `git` (for cloning the repository)
*   `make` (for using the command shortcuts)

### Step 2: Clone and Configure

```bash
# 1. Clone the repository to your local machine
git clone <your-repo-url>
cd Project-Cortex-MK1 # Or your chosen directory name

# 2. Create your local environment file from the example
# This file is ignored by git and holds your local secrets and configuration.
cp .env.example .env
```
**➡️ IMPORTANT:** Open the `.env` file you just created. You must edit this file to set your desired passwords, ports, and other configuration variables. The default values are placeholders.

### Step 3: Core `make` Commands

The `Makefile` is your primary interface for managing the application stack.

| Command                     | Description                                                                                             | Example Usage             |
| :-------------------------- | :------------------------------------------------------------------------------------------------------ | :------------------------ |
| `make up`                   | Builds images if they don't exist and starts all services in detached mode.                             | `make up`                 |
| `make down`                 | Stops and removes all service containers and the default network.                                       | `make down`               |
| `make restart`              | A convenient shortcut for `make down && make up`.                                                       | `make restart`            |
| `make re`                   | Forces a full rebuild of all Docker images and then restarts the stack. Use this after changing code.   | `make re`                 |
| `make logs`                 | Follows the logs of all running services. Press `Ctrl+C` to exit.                                       | `make logs`               |
| `make logs service=<name>`  | Follows the logs of a specific service (e.g., `app`, `api_gateway`, `neo4j`).                           | `make logs service=app`   |
| `make ssh service=<name>`   | Opens an interactive shell (`/bin/sh` or `/bin/bash`) inside a running container. Incredibly useful for debugging. | `make ssh service=neo4j`  |
| `make status`               | Shows the current status (running, stopped, etc.) of all services.                                      | `make status`             |
| `make test`                 | Runs the latency benchmark script inside a temporary container.                                         | `make test`               |
| `make clean`                | Same as `make down`.                                                                                    | `make clean`              |
| `make fclean`               | Stops and removes containers, networks, **and all associated volumes** defined in `docker-compose.yml`. | `make fclean`             |
| `make prune`                | The ultimate cleanup. Runs `fclean` and then prunes all unused Docker assets from your system.          | `make prune`              |

### Step 4: Verification

1.  Run `make up`.
2.  After a minute (to allow services to start and pass health checks), run `make status`. You should see all services (`api_gateway`, `app`, `neo4j`, `redis`) in the `running` state.
3.  Navigate to `http://localhost:7474` in your browser to see the Neo4j Browser interface. You can log in with the user `neo4j` and the password you set in your `.env` file.
4.  You are now ready to interact with the API Gateway.

---

## 🔌 API Deep Dive & Usage Examples

The gateway uses standardized Pydantic models for all communication.

**`InferenceRequest` Model:**
```python
# From: api_gateway/models.py
class InferenceMessage(BaseModel):
    role: str
    content: str

class InferenceInput(BaseModel):
    messages: List[InferenceMessage]

class InferenceRequest(BaseModel):
    user_id: str = Field(..., description="The user ID.")
    provider: str = Field(..., description="The name of the backend service provider (e.g., 'graphrag-app').")
    model: Optional[str] = Field(None, description="The specific model to use from the provider.")
    input: InferenceInput
    stream: bool = Field(default=False, description="Whether to stream the response.")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Provider-specific parameters.")
```

### Usage Examples

#### Example 1: Non-Streaming REST Request

Use `curl` to send a standard HTTP POST request. Note the `provider` field is still `graphrag-app` as this refers to the backend service name in the Docker network.

```bash
curl -X POST http://localhost:8080/v1/inference \
-H "Content-Type: application/json" \
-d '{
  "user_id": "test-user-123",
  "provider": "graphrag-app",
  "stream": false,
  "input": {
    "messages": [
      {
        "role": "user",
        "content": "Hello, what can you do?"
      }
    ]
  }
}'
```

#### Example 2: Streaming WebSocket Request

Use a command-line tool like `wscat` to interact with the streaming endpoint.

1.  **Install `wscat`:** `npm install -g wscat`

2.  **Connect to the WebSocket:**
    ```bash
    wscat -c ws://localhost:8080/v1/inference/stream
    ```

3.  **Send the initial `InferenceRequest` message:**
    Once connected, paste the following JSON and press Enter. This tells the gateway you want to start a streaming session with the `graphrag-app` provider.

    ```json
    {
      "user_id": "test-user-ws",
      "provider": "graphrag-app",
      "stream": true,
      "input": {
        "messages": [
          {
            "role": "user",
            "content": "This is my first message."
          }
        ]
      }
    }
    ```

4.  **Interact:** You will receive response messages from the server. For a voice stream, you would send raw audio bytes after this initial handshake. For a text stream, you would send subsequent text messages.

---

## 🔧 Customization: Adding a New Provider to Cortex

The gateway's provider architecture makes it simple to add new backend services. Let's say you want to add a provider for a local Ollama instance.

1.  **Update `config.yml`**:
    Add your new service to `api_gateway/config.yml`.

    ```yaml
    services:
      - name: "graphrag-app"
        # ... (existing config)
      - name: "ollama-local"
        prefix: "/ollama"
        upstream_url: "http://host.docker.internal:11434" # Assuming Ollama runs on your host machine
        inference_path: "/api/chat"
    ```

2.  **Implement Transformation Logic**:
    Open `api_gateway/transformers.py` and add new cases for your provider.

    ```python
    # In transform_request function
    def transform_request(provider: str, request: InferenceRequest) -> dict:
        if provider == "graphrag-app":
            # ...
        elif provider == "ollama-local":
            # Convert the standard request to Ollama's format
            return {
                "model": request.model or "llama3",
                "messages": [msg.dict() for msg in request.input.messages],
                "stream": request.stream
            }
        else:
            return request.dict()

    # In transform_response function
    def transform_response(provider: str, response: dict) -> InferenceResponse:
        if provider == "graphrag-app":
            # ...
        elif provider == "ollama-local":
            # Convert Ollama's response back to the standard format
            return InferenceResponse(
                id=response.get("id", "some_ollama_id"),
                provider=provider,
                model=response.get("model", "llama3"),
                output={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response.get("message", {}).get("content", "")
                        }
                    }]
                }
            )
        else:
            return InferenceResponse(**response)
    ```

3.  **Restart and Use**:
    Restart the gateway (`make restart service=api_gateway`). You can now send requests to the gateway with `"provider": "ollama-local"`. The gateway will handle the routing and transformation automatically.

---

## 🗺️ Cortex: The Future Roadmap

Cortex is an ambitious project under active development. Our roadmap is broken down into key milestones that build upon each other to create a truly next-generation AI platform.

### 🎯 Milestone 1: Gateway Foundation & First-Party Integration `(In Progress)`

*   **Vision**: To build a robust, production-ready gateway and fully integrate the GraphRAG service as its first-class citizen, showcasing the power of the core architecture.
*   **Key Deliverables**:
    *   `[x]` **Standardized Models**: Define the universal `InferenceRequest` and `InferenceResponse` models that will form the bedrock of the entire system.
    *   `[x]` **Core Gateway Logic**: Implement the HTTP and WebSocket endpoints with provider-based routing and the transformation layer.
    *   `[ ]` **Formal Provider Interface**: Refactor the `GraphRAG` backend into a formal `Provider` class that implements a standardized interface, serving as a template for all future providers.
    *   `[ ]` **Enhanced Agentic Capabilities**: Move beyond placeholder LLM responses. Integrate a true streaming LLM (e.g., from Groq, Together AI, or a local model) to enable dynamic, intelligent conversation. Implement status updates (`"Searching knowledge graph..."`, `"Synthesizing response..."`) to provide transparency into the agent's thought process.

### 🎯 Milestone 2: Third-Party Providers & The Security Plane

*   **Vision**: To expand the gateway from a single-service orchestrator into a true multi-provider ecosystem, and to harden it with enterprise-grade security and access control.
*   **Key Deliverables**:
    *   `[ ]` **External Provider Integrations**: Systematically add providers for major AI services.
        *   **OpenAI Provider**: Full support for GPT-4, GPT-3.5, and other models, with secure API key management.
        *   **Anthropic Provider**: Integration with the Claude 3 model family (Haiku, Sonnet, Opus).
        *   **Local Model Provider**: A first-class provider for `Ollama`, enabling seamless use of local models like Llama 3 and Mistral.
    *   `[ ]` **Centralized Authentication (AuthN)**: Implement JWT-based authentication at the gateway. The gateway will be responsible for validating tokens and propagating user identity securely to the backend services.
    *   `[ ]` **Centralized Authorization (AuthZ)**: Integrate a policy-based access control system (e.g., Open Policy Agent). This will allow for granular control, defining policies such as "User A can access Provider X but not Provider Y," or "User B can only use the low-cost models."
    *   `[ ]` **Rate Limiting & Throttling**: Implement a Redis-based rate limiting mechanism to prevent abuse, manage costs, and ensure fair usage, with configurable per-user and per-provider limits.

### 🎯 Milestone 3: Production Readiness & Advanced Features

*   **Vision**: To evolve the platform from a functional system to a highly available, observable, and feature-rich service ready for mission-critical deployments.
*   **Key Deliverables**:
    *   `[ ]` **The Observability Stack**:
        *   **Centralized Logging**: Implement structured (JSON) logging across all services and ship logs to a centralized platform like the ELK stack or Grafana Loki for powerful querying and analysis.
        *   **Metrics & Monitoring**: Expose Prometheus metrics from the gateway (request latency, error rates, active streams) and create a comprehensive Grafana dashboard for at-a-glance system health monitoring.
    *   `[ ]` **Advanced Caching**: Implement a semantic caching layer at the gateway. This goes beyond simple key-value caching by using embeddings to determine if a new query is semantically similar to a previously answered one, allowing the gateway to serve a cached response and dramatically reduce costs and latency.
    *   `[ ]` **Edge Deployment**: Create and test official ARM64 builds of the GraphRAG service, enabling deployment on low-power edge devices like the NVIDIA Jetson and Raspberry Pi for fully self-contained, offline-capable agents.
    *   `[ ]` **Comprehensive Testing Suite**: Go beyond basic tests. Add a full end-to-end load testing suite using tools like k6 or Locust to identify performance bottlenecks under pressure and ensure the system can scale.

### 🚀 The Long-Term Vision: Beyond Milestones

*   **Autonomous Agent Swarms**: Evolve the gateway into an agent-to-agent communication bus, allowing specialized agents (a "research agent," a "coding agent," a "data analysis agent") to collaborate on complex tasks.
*   **Federated Knowledge Graphs**: Develop a mechanism for agents to securely and privately query and share knowledge from each other's knowledge graphs, creating a decentralized, collective intelligence.
*   **Zero-Configuration Deployment**: Create automated deployment scripts and Helm charts for one-command deployment to Kubernetes clusters, both in the cloud and on-premises.
*   **Self-Improving Systems**: Implement a feedback loop where the system analyzes its own performance and conversations to automatically identify gaps in its knowledge graph, fine-tune its models, and improve its predictive caching accuracy over time.

---

## 🤝 Contributing

This is an ambitious project, and contributions are welcome. Please refer to the `TODO.md` for the current development roadmap.

1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature/your-feature-name`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
