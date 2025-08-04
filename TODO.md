# TODO Roadmap

This file tracks the development progress of the Universal AI Gateway and its backend services.

---

## 🎯 Milestone 1: Gateway Foundation & First-Party Integration

*Goal: Establish a robust, production-ready gateway and fully integrate the GraphRAG service.* 

### 🚀 Core Gateway (`api_gateway/`)

- [ ] **Architect the Provider Interface**
  - [x] Define standardized `InferenceRequest` and `InferenceResponse` models.
  - [ ] Design an abstract base class (`InferenceProvider`) for all clients.
    - [ ] Define `infer()` method for non-streaming responses.
    - [ ] Define `stream_infer()` method for streaming, including status updates.
  - [ ] Implement a provider registry for auto-discovery.

- [ ] **Develop Gateway Logic**
  - [x] Implement `/v1/inference` endpoint for HTTP requests.
  - [x] Implement `/v1/inference/stream` endpoint for WebSocket communication.
  - [x] Implement routing logic to select the correct provider.
  - [x] Implement the transformation layer for requests and responses.

- [ ] **Containerization & Deployment**
  - [x] Create `Dockerfile` for the gateway.
  - [x] Integrate the gateway into the main `docker-compose.yml`.
  - [ ] Add a production-ready `docker-compose.prod.yml` with NGINX.

### 🗣️ GraphRAG Backend (`app/`)

- [ ] **Refactor for Gateway Compatibility**
  - [ ] Create a `GraphRAGProvider` class that implements the `InferenceProvider` interface.
  - [ ] Adapt the `agent.py` and `voice.py` endpoints to conform to the standardized input/output formats.

- [ ] **Enhance Agentic Capabilities**
  - [ ] **LLM Integration**: Add a streaming LLM for more dynamic response generation.
    - [ ] Research and select a suitable streaming LLM (e.g., Groq, Together AI).
    - [ ] Implement a client for the selected LLM.
    - [ ] Integrate the LLM into the `LiveAgentService`.
  - [ ] **Status Updates**: Emit status updates during the RAG process (e.g., "Searching knowledge graph," "Synthesizing response").

---

## 🎯 Milestone 2: Third-Party Providers & Security

*Goal: Expand the ecosystem with external providers and harden the gateway.* 

### 🔌 Provider Integrations

- [ ] **Add OpenAI Provider**
  - [ ] Implement `OpenAIProvider` class.
  - [ ] Add transformation logic for GPT-3.5 and GPT-4 models.
  - [ ] Handle API key management securely.

- [ ] **Add Anthropic Provider**
  - [ ] Implement `AnthropicProvider` class.
  - [ ] Add transformation logic for Claude 3 models (Haiku, Sonnet, Opus).

- [ ] **Add Local Model Provider (e.g., Ollama)**
  - [ ] Implement `OllamaProvider` class.
  - [ ] Add transformation logic for popular local models (e.g., Llama 3, Mistral).

### 🛡️ Security & Control Plane

- [ ] **Implement Centralized Authentication**
  - [ ] Add JWT-based authentication to the gateway.
  - [ ] Implement token validation and user identity propagation.

- [ ] **Implement Centralized Authorization**
  - [ ] Add a policy-based access control system (e.g., OPA).
  - [ ] Define policies for which users can access which providers/sources.

- [ ] **Implement Rate Limiting & Throttling**
  - [ ] Add a rate limiting mechanism to prevent abuse.
  - [ ] Implement per-user and per-provider rate limits.

---

## 🎯 Milestone 3: Production Readiness & Advanced Features

*Goal: Make the system highly available, observable, and feature-rich.* 

### 📈 Observability & Testing

- [ ] **Implement Centralized Logging**
  - [ ] Add structured logging (e.g., JSON) to the gateway and backend services.
  - [ ] Ship logs to a centralized logging platform (e.g., ELK stack, Grafana Loki).

- [ ] **Implement Metrics & Monitoring**
  - [ ] Expose Prometheus metrics from the gateway (e.g., request latency, error rates).
  - [ ] Create a Grafana dashboard for monitoring gateway performance.

- [ ] **Comprehensive Testing**
  - [ ] Add unit tests for all gateway components.
  - [ ] Add integration tests for each provider.
  - [ ] Add end-to-end tests for common user flows.
  - [ ] Perform load testing to identify performance bottlenecks.

### ✨ Advanced Features

- [ ] **Implement Centralized Caching**
  - [ ] Add a Redis-based caching layer to the gateway.
  - [ ] Implement semantic caching for similar queries to reduce costs.

- [ ] **Multi-language Support (GraphRAG)**
  - [ ] Add support for more languages in the voice pipeline.
  - [ ] Test the multilingual capabilities end-to-end.

- [ ] **Edge Deployment (GraphRAG)**
  - [ ] Create ARM64 builds for the GraphRAG service.
  - [ ] Test deployment on an ARM64 device (e.g., Raspberry Pi, NVIDIA Jetson).