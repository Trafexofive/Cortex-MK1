# Universal AI Gateway & Agent MK1

This project provides a **Universal AI Gateway**, a unified entry point for accessing and orchestrating a wide range of AI models, agents, and workflows. It acts as a central control plane for a larger AI ecosystem, providing a standardized interface for both streaming and non-streaming AI services.

One of the primary backend services provided is the **GraphRAG-Agent-MK1**, a blazing-fast, low-latency Graph RAG implementation for live voice agents.

## The Vision: A Unified AI Ecosystem

The gateway is designed to abstract away the complexity of various AI providers and services. Developers can build applications that consume AI capabilities through a single, consistent API, without needing to know the specifics of the underlying implementation.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Provider   │    │ Universal AI    │    │   Your Custom   │
│ (OpenAI, etc.)  │◄──►│    Gateway      │◄──►│  AI Service     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web App       │    │   Mobile App    │    │   Voice Agent   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

# GraphRAG-Agent-MK1: The Voice-Enabled Backend

The GraphRAG-Agent-MK1 is a powerful backend service that provides a complete, low-latency solution for building voice-driven conversational agents.

- **Streaming Voice Pipeline**: ~100-200ms voice-to-voice response
- **Predictive Response Generation**: Start generating while user speaks
- **Memory-Mapped Models**: Everything stays in RAM
- **Parallel Processing**: Transcribe + Generate + Retrieve simultaneously
- **Smart Caching**: Pre-computed embeddings and phonemes

## Project Structure

```
graph-rag-agent-mk1/
├── README.md
├── docker-compose.yml
├── api_gateway/
│   ├── main.py
│   └── ...
├── app/ # The GraphRAG application
│   ├── main.py
│   └── ...
└── ...
```

## Getting Started

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- CMake (for whisper.cpp)
- Git

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd graph-rag-agent-mk1
cp .env.example .env
```

### 2. Environment Variables (.env)
Fill in the required variables in the `.env` file.

### 3. Start Services
```bash
docker-compose up -d
```

## Technical Deep Dive: GraphRAG-Agent-MK1

### Ultra-Fast Voice Service (app/core/voice_pipeline.py)
The voice pipeline is designed for ultra-low latency, featuring a streaming architecture that processes audio in small chunks. It uses `whisper.cpp` for transcription and `Piper TTS` for synthesis.

### Predictive Context Loading (app/core/graph_rag.py)
The Graph RAG engine uses a predictive context loading mechanism to anticipate the user's next queries, pre-loading relevant information from the knowledge graph to reduce retrieval times.

### Latency Targets
- **Voice Input**: <100ms (whisper.cpp streaming)
- **Graph Retrieval**: <50ms (cached paths + parallel queries)
- **Voice Output**: <50ms (Piper TTS streaming)
- **Total Voice-to-Voice**: <200ms