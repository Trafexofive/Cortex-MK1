# TODO

This file tracks the development progress of the GraphRAG-Agent-MK1 project.

## Future

- [ ] **LLM Integration**: Add streaming LLM for response generation.
  - [ ] Research and select a suitable streaming LLM.
  - [x] Implement the LLM integration in `app/services/live_agent.py`.
  - [x] Add a new service for the LLM in `app/services/llm_service.py`.
- [x] **Voice Cloning**: Personal voice models per user.
  - [x] Research voice cloning libraries.
  - [x] Implement voice cloning functionality.
- [ ] **Multi-language**: Whisper multilingual + international TTS.
  - [x] Add support for multiple languages in `app/core/voice_pipeline.py`.
  - [ ] Test the multilingual capabilities.
- [ ] **Edge Deployment**: ARM64 builds for edge computing.
  - [ ] Create a new Dockerfile for ARM64 builds.
  - [ ] Test the deployment on an ARM64 device.
- [ ] **Advanced Caching**: Semantic caching for graph contexts.
  - [ ] Implement semantic caching in `app/core/graph_rag.py`.
- [ ] **A/B Testing**: Voice quality vs latency optimization.
  - [ ] Implement A/B testing framework.

## In Progress

- [x] **Initial Setup**: Basic project structure and dependencies.
  - [x] Initialize Git repository.
  - [x] Create `README.md` and `.gitignore`.
  - [x] Set up `requirements.txt`.
- [x] **Core Voice Pipeline**: Implement the main voice processing logic.
  - [x] Integrate `whisper.cpp` for transcription.
  - [x] Integrate `Piper TTS` for synthesis.
  - [x] Create `app/core/voice_pipeline.py`.

## Done

- [x] **Neo4j and Redis Integration**: Set up database and cache connections.
  - [x] Create `app/core/neo4j_client.py`.
  - [x] Create `app/core/redis_client.py`.
- [x] **FastAPI Setup**: Create the main API and endpoints.
  - [x] Create `app/main.py`.
  - [x] Add health check endpoint in `app/api/routes/health.py`.
- [x] **GraphRAG Engine**: Initial implementation of the RAG logic.
  - [x] Create `app/core/graph_rag.py`.
- [x] **Dockerization**: Create Dockerfile and docker-compose.yml.
  - [x] Write `Dockerfile`.
  - [x] Write `docker-compose.yml`.
