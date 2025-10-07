# ══════════════════════════════════════════════════════════════════════════════
# DOCKER DEPLOYMENT GUIDE - Chat Test Service
# ══════════════════════════════════════════════════════════════════════════════

## Quick Start

### 1. Start with Docker (Recommended)

```bash
# Start the service
./start_chat_test.sh

# This will:
# - Build the Docker container
# - Start the service on port 8888
# - Make it available at http://localhost:8888
```

### 2. Start Locally (Development)

```bash
# Run without Docker
./start_chat_test_local.sh

# This will:
# - Install dependencies if needed
# - Run the service directly with Python
# - Start on http://localhost:8888
```

## Access the Service

Open your browser to: **http://localhost:8888**

You'll see a beautiful chat interface ready to test the streaming protocol!

## Manual Docker Commands

```bash
# Build only
docker-compose build chat_test

# Start service
docker-compose up -d chat_test

# View logs
docker-compose logs -f chat_test

# Stop service
docker-compose down chat_test

# Restart
docker-compose restart chat_test

# Rebuild and restart
docker-compose up -d --build chat_test
```

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# Optional: Add Gemini API key for real LLM
GEMINI_API_KEY=your_api_key_here

# Port configuration
CHAT_TEST_HOST_PORT=8888
```

If no `GEMINI_API_KEY` is provided, the service uses a mock LLM that demonstrates the protocol.

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Container                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FastAPI Service (Port 8888)                          │  │
│  │  • SSE Streaming endpoint                             │  │
│  │  • Embedded HTML chat UI                              │  │
│  │  • Health check endpoint                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Streaming Protocol Parser                            │  │
│  │  • Parses <thought>, <action>, <response> tags        │  │
│  │  • Executes actions as they're parsed                 │  │
│  │  • Manages dependencies                               │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Mock Tools                                           │  │
│  │  • web_scraper                                        │  │
│  │  • calculator                                         │  │
│  │  • arxiv_search                                       │  │
│  │  • database_query                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  LLM (Mock or Gemini)                                 │  │
│  │  • Generates streaming responses                      │  │
│  │  • Uses protocol format                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕
                     Browser Client
                  (SSE EventSource)
```

## File Structure

```
services/chat_test/
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
├── chat_test_service.py          # Main service (FastAPI + UI)
├── runtime_executor/             # Protocol parser
│   ├── __init__.py
│   └── streaming_protocol_parser.py
└── README.md                     # This file
```

## Docker Image Details

- **Base**: `python:3.11-slim`
- **Exposed Port**: 8888
- **Health Check**: `http://localhost:8888/health`
- **Dependencies**: FastAPI, Uvicorn, Pydantic, google-generativeai

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8888
lsof -i :8888

# Stop the service
docker-compose down chat_test

# Or change the port in .env
CHAT_TEST_HOST_PORT=8889
```

### Container Won't Start

```bash
# Check logs
docker-compose logs chat_test

# Rebuild from scratch
docker-compose down chat_test
docker-compose build --no-cache chat_test
docker-compose up -d chat_test
```

### Import Errors

The service includes the streaming protocol parser in the container.
If you see import errors:

```bash
# Verify the parser was copied
docker-compose exec chat_test ls -la runtime_executor/

# Should show:
# streaming_protocol_parser.py
```

## Testing the Service

### 1. Health Check

```bash
curl http://localhost:8888/health
# Expected: {"status":"healthy","service":"chat-test"}
```

### 2. Chat Interface

1. Open http://localhost:8888
2. Type a message: "Tell me about AI"
3. Watch the streaming response with:
   - 💭 Thoughts (yellow)
   - 🔄 Actions (blue)
   - 📝 Response (green)

### 3. Example Queries

Try these to see different protocol features:

- **"What is 42 + 8?"** - See calculator action
- **"Search arXiv for machine learning"** - See search action
- **"Tell me about quantum computing"** - See multiple parallel actions
- **"Analyze the latest AI research"** - See dependencies between actions

## Integration with Other Services

This service can be extended to connect with other Cortex services:

```yaml
# In docker-compose.yml
chat_test:
  depends_on:
    - runtime_executor
    - manifest_ingestion
  networks:
    - cortex_prime_network
```

Then update the service to call real tools instead of mocks.

## Development Mode

For development with auto-reload:

```bash
# Edit docker-compose.yml to add:
volumes:
  - ./services/chat_test:/app

# Then restart
docker-compose restart chat_test
```

Changes to Python files will trigger auto-reload.

## Production Deployment

For production:

1. Remove the volume mount (use baked-in code)
2. Add proper logging
3. Configure HTTPS/TLS
4. Set resource limits
5. Add monitoring

```yaml
chat_test:
  build:
    context: ./services/chat_test
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 512M
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

## Next Steps

1. ✅ Start the service
2. ✅ Test the chat interface
3. ✅ Verify streaming protocol works
4. ⬜ Integrate with real tools
5. ⬜ Connect to runtime_executor service
6. ⬜ Add authentication
7. ⬜ Deploy to production

---

**Ready to test?** Run `./start_chat_test.sh` now!
