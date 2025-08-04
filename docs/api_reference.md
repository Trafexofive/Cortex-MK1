# API Reference

## Universal AI Gateway

The API Gateway provides a standardized set of endpoints for interacting with various AI services.

### Endpoints

*   `POST /v1/inference`

    The main endpoint for non-streaming inference requests. It accepts a standardized `InferenceRequest` and returns a standardized `InferenceResponse`.

*   `WS /v1/inference/stream`

    The WebSocket endpoint for streaming inference requests. It allows for real-time, bidirectional communication with the backend service, and supports status updates for agentic workflows.

*   `GET /health`

    A simple health check endpoint for the gateway.

## Backend Services

The API Gateway routes requests to various backend services. The original GraphRAG application is one such service, and it exposes the following endpoints:

*   `WS /agent/stream/{user_id}`: WebSocket endpoint for agent interaction.
*   `WS /voice/stream/{user_id}`: WebSocket endpoint for voice interaction.
*   `POST /knowledge/upload`: Endpoint for uploading knowledge documents.