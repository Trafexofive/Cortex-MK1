
***

# 🚀 Universal AI Gateway & Agent MK1

### "The distance between thought and action, minimized."

This repository contains the **Universal AI Gateway**, a production-grade, high-performance control plane for orchestrating any AI service, model, or workflow. It provides a single, standardized, and extensible API for your entire AI ecosystem.

Its premier backend is the **GraphRAG-Agent-MK1**: a voice-first conversational agent with a sub-200ms voice-to-voice latency, built on a streaming, predictive GraphRAG engine. It's not just fast; it's designed for real-time, natural human interaction.

<br>

<p align="center">
  <img src="https://i.imgur.com/g8e1z6Z.png" alt="Architecture Diagram" width="800"/>
</p>

---

##  filozofie

This project is built on a set of core axioms that guide its architecture and development:

*   **Efficiency & Flow**: Every component is optimized for extreme low-latency. The system is designed to never interrupt the user's creative or conversational flow.
*   **Compositional Design**: The system is composed of simple, interchangeable components (`api_gateway`, `app`, `neo4j`, `redis`). This allows for scalability, maintainability, and easy extension.
*   **Developer Experience**: A Docker-centric workflow and a comprehensive `Makefile` provide a single, simple interface for setup, management, and debugging.
*   **Technical Integrity**: No shortcuts. The architecture is clean, the code is organized, and every dependency is chosen for performance and reliability.

---

## ✨ Core Features

| Universal AI Gateway                                                                                                                                                                                                                                                                                                                                | GraphRAG-Agent-MK1 (Backend)                                                                                                                                                                                                                                                                                                                                                                                                                   |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Unified API**: A single `/v1/inference` endpoint for all AI interactions, supporting both REST (`POST`) and real-time streaming (`WebSocket`).                                                                                                                                                                                                       | **<200ms Voice-to-Voice Latency**: A fully streaming pipeline for transcription, graph retrieval, LLM generation, and speech synthesis enables truly natural conversation.                                                                                                                                                                                                                                                                                            |
| **Pluggable Provider Architecture**: A `config.yml`-driven system for seamlessly integrating any AI service—OpenAI, Anthropic, local models via Ollama, or your own custom services.                                                                                                                                                                 | **Predictive Graph RAG Engine**: Anticipates follow-up questions and pre-fetches context from the Neo4j knowledge graph into a Redis cache *before* you even ask.                                                                                                                                                                                                                                                                                               |
| **Automated Transformation Layer**: Automatically transforms the standardized `InferenceRequest` and `InferenceResponse` models to and from provider-specific formats, eliminating boilerplate code.                                                                                                                                                     | **High-Performance Voice Tech**: Uses `whisper.cpp` for ultra-fast, low-footprint transcription and `Piper TTS` for clear, natural speech synthesis with minimal time-to-first-sound.                                                                                                                                                                                                                                                                          |
| **Centralized Control Plane**: Provides the ideal point to implement cross-cutting concerns like authentication, rate limiting, centralized logging, and semantic caching. (See Roadmap).                                                                                                                                                              | **Dynamic Knowledge Ingestion**: A live `/knowledge/upload` endpoint allows for adding documents to the agent's knowledge graph on the fly.                                                                                                                                                                                                                                                                                                                        |
| **Containerized & Production-Ready**: Built with FastAPI and fully containerized with Docker and Docker Compose, including health checks and restart policies for robust, scalable deployments. A `docker-compose.prod.yml` and Kubernetes manifests are also provided. | **Multi-modal and Multi-lingual**: Distinct WebSocket endpoints for voice (`/voice/stream`) and text-based (`/agent/stream`) interaction. Designed for multilingual support from the ground up, with initial tests for English and Spanish. |

---

## 🏛️ Architecture & Data Flow

The system is architected as a set of cooperating microservices, orchestrated by Docker Compose.

1.  **Client Connection**: A user connects to the **API Gateway** via WebSocket (`/v1/inference/stream`). The initial message specifies the desired provider (e.g., `graphrag-app`).
2.  **Request Routing**: The Gateway validates the request and proxies it to the appropriate backend service defined in `api_gateway/config.yml`—in this case, the `app` service's voice stream endpoint.
3.  **Voice-to-Text (Transcription)**: The `app` service's `VoicePipeline` receives raw audio bytes. It streams this audio to `whisper.cpp`, which performs real-time transcription.
4.  **Parallel Processing (RAG + Prediction)**: As soon as a transcript is generated, the `LiveAgentService` triggers two parallel actions:
    *   **Graph Retrieval**: The `GraphRAGEngine` converts the transcript to an embedding and queries the `Neo4j` graph database for relevant context. Results from `Neo4j` are cached in `Redis` to accelerate future lookups.
    *   **Follow-up Prediction**: Simultaneously, a lightweight model predicts likely follow-up questions. The system preemptively runs `retrieve` for these predicted queries, warming the cache.
5.  **LLM Response Generation**: The retrieved context is passed to the `LLMService`, which streams a response back to the agent.
6.  **Text-to-Voice (Synthesis)**: The `VoicePipeline` takes the generated text response and streams it to `Piper TTS` for real-time speech synthesis.
7.  **Response Streaming**: The synthesized audio bytes are streamed back through the **API Gateway** to the client.

This entire process occurs in a continuous, streaming fashion, ensuring that the user hears the agent's response with minimal perceptible delay.

---

## ⚡ Technology Stack

| Component           | Technology                                                                          | Rationale                                                                        |
| :------------------ | :---------------------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
| **API Gateway & App** | **[FastAPI](https://fastapi.tiangolo.com/)**                                        | High performance, native async support, WebSocket handling, and Pydantic integration.    |
| **Graph Database**    | **[Neo4j](https://neo4j.com/)**                                                     | Ideal for modeling and querying complex, interconnected data for the RAG engine.         |
| **Caching Layer**     | **[Redis](https://redis.io/)**                                                      | In-memory data store for sub-millisecond latency on cached queries and predictions.      |
| **Containerization**  | **[Docker](https://www.docker.com/) & Docker Compose**                              | For reproducible builds, isolated environments, and simplified service orchestration. |
| **Transcription**     | **[whisper.cpp](https://github.com/ggerganov/whisper.cpp)**                         | State-of-the-art speech-to-text with minimal resource footprint and high performance.   |
| **Speech Synthesis**  | **[Piper TTS](https://github.com/rhasspy/piper)**                                   | Fast, high-quality, and local text-to-speech synthesis.                            |
| **Data Models**       | **[Pydantic](https://docs.pydantic.dev/)**                                          | For robust data validation, settings management, and clear data contracts.        |

---

## 🛠️ Getting Started

Management of the entire stack is handled via the `Makefile`.

### 1. Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
*   `git`
*   `make`

### 2. Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd GraphRAG-Agent-MK1

# Create your local environment file from the example
cp .env.example .env
```
**--> IMPORTANT:** Open and edit the `.env` file to set your desired passwords, ports, and other configuration variables.

### 3. Run the Stack

```bash
# Build all images and start all services in detached mode.
# This is the recommended command for the first run.
make up

# To check the status of all running services
make status

# To stream the logs of all services
make logs

# To stream the logs of a single service (e.g., the app)
make logs service=app

# To get a shell inside a running service (e.g., the app)
make ssh service=app

# To stop and remove all containers, networks, and volumes
make down --volumes
```

### 4. Ultimate Cleanup

To perform a complete system purge, stopping all services, removing all volumes, and pruning all unused Docker assets:
```bash
make prune
```

---

## 🗺️ Future Roadmap

This project is ambitious and under active development. Here are the key milestones on our immediate horizon.

### 🎯 Milestone 1: Gateway Foundation & First-Party Integration `(In Progress)`

*   **Goal**: Establish a production-ready gateway and fully integrate the GraphRAG service.
*   **Key Tasks**:
    *   `[x]` Architect the standardized `InferenceRequest`/`InferenceResponse` models.
    *   `[x]` Implement the core gateway routing and transformation logic for HTTP and WebSockets.
    *   `[ ]` Refactor the `GraphRAG` backend into a formal `Provider` class.
    *   `[ ]` **Enhance Agentic Capabilities**: Integrate a true streaming LLM (e.g., Groq, Together) and emit status updates during the RAG process (e.g., *"Searching knowledge graph..."*).

### 🎯 Milestone 2: Third-Party Providers & Security

*   **Goal**: Expand the ecosystem with external providers and harden the gateway's security.
*   **Key Tasks**:
    *   `[ ]` **Provider Integrations**: Implement providers for OpenAI (GPT-4), Anthropic (Claude 3), and local models via Ollama.
    *   `[ ]` **Centralized AuthN/AuthZ**: Implement JWT-based authentication and a policy-based access control system (e.g., OPA) at the gateway level.
    *   `[ ]` **Rate Limiting & Throttling**: Add per-user and per-provider rate limiting to prevent abuse and manage costs.

### 🎯 Milestone 3: Production Readiness & Advanced Features

*   **Goal**: Make the system highly available, observable, and feature-rich.
*   **Key Tasks**:
    *   `[ ]` **Observability Stack**: Implement centralized, structured logging (ELK/Loki) and expose Prometheus metrics with a Grafana dashboard for monitoring gateway performance.
    *   `[ ]` **Centralized Caching**: Implement a semantic caching layer in the gateway to reduce costs by serving cached responses for similar queries across all providers.
    *   `[ ]` **Edge Deployment**: Create and test ARM64 builds for deploying the GraphRAG service on edge devices like the NVIDIA Jetson or Raspberry Pi.
    *   `[ ]` **Comprehensive Testing**: Add full unit, integration, and end-to-end load testing to identify and eliminate performance bottlenecks.

---

## 📜 API Quick Reference

The gateway exposes a simple, powerful API.

*   `POST /v1/inference`
    *   The main endpoint for non-streaming inference requests.
    *   **Body**: `InferenceRequest`
    *   **Returns**: `InferenceResponse`

*   `WS /v1/inference/stream`
    *   The WebSocket endpoint for real-time, bidirectional streaming.
    *   **Protocol**: Send an `InferenceRequest` JSON message upon connection, then stream data.

*   `GET /health`
    *   A simple health check endpoint for monitoring.
