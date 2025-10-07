# Chat Test Service - Quick Start

## Docker (Recommended)

```bash
# Start the service
./start_chat_test.sh

# Or manually
docker-compose up -d chat_test

# View logs
docker-compose logs -f chat_test

# Stop
docker-compose down chat_test
```

Access at: **http://localhost:8888**

## Local Development

```bash
# Run locally without Docker
./start_chat_test_local.sh
```

## What You Get

- 💬 Beautiful chat interface
- 🔄 Real-time streaming protocol
- 🧪 Mock tools (no API keys needed)
- 🤖 Optional Gemini integration

## Configuration

Edit `.env` to add Gemini API key:
```
GEMINI_API_KEY=your_key_here
```

Otherwise uses mock LLM.

## Architecture

```
Browser (UI)
    ↓ SSE Stream
FastAPI Service
    ↓ Tokens
StreamingProtocolParser
    ↓ Actions
Mock Tools
    ↓
LLM (Mock or Gemini)
```

See `CHAT_TEST_README.md` for full documentation.
