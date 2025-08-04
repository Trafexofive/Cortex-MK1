# Architecture

## The Universal AI Gateway

The project is architected around a central **Universal AI Gateway**. This gateway serves as a unified entry point for all AI-related services, providing a standardized interface for developers and enabling seamless integration of various backend providers.

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

### Core Components

*   **API Gateway (`api_gateway/`)**: A FastAPI application that exposes a standardized `/v1/inference` endpoint. It handles both HTTP and WebSocket communication, and is responsible for routing requests to the appropriate backend service.

*   **Pluggable Providers**: The gateway uses a provider-based architecture, where each backend service is treated as a "provider." This allows for easy integration of new services by simply adding a new provider configuration to `config.yml` and implementing the necessary transformation logic.

*   **Standardized Models (`api_gateway/models.py`)**: The gateway uses a set of standardized Pydantic models for requests and responses. This ensures a consistent API structure across all providers.

*   **Transformation Layer (`api_gateway/transformers.py`)**: The gateway includes a transformation layer that converts the standardized request and response formats to and from the provider-specific formats. This is the key to the gateway's flexibility.

### Backend Services

*   **GraphRAG Agent (`app/`)**: The original GraphRAG application is now a backend service that can be accessed through the API gateway. It provides a low-latency, voice-enabled RAG implementation.

*   **Other AI Services**: The gateway is designed to be easily extended to support other AI services, such as commercial LLMs (OpenAI, Anthropic), open-source models, or custom-built AI workflows.