# Cortex-CLI: CLI Bash Client

**End-to-end command-line interface for chatting with agents loaded from local manifests.**

## Overview

Cortex-CLI is a fully integrated CLI client that:

1. ✅ Loads agent manifests via the **manifest_ingestion** service
2. ✅ Validates and parses agent configuration
3. ✅ Connects to the **LLM gateway** for actual inference
4. ✅ Provides interactive chat with streaming responses
5. ✅ Supports all agent cognitive engine configurations

This is a **real e2e client** - not a mock. It integrates with the actual Cortex-Prime services.

## Prerequisites

The following services must be running:
- **manifest_ingestion** (port 8082)
- **runtime_executor** (port 8083)
- **llm_gateway** (port 8081)

Start services with:
```bash
cd infra
docker-compose up -d manifest_ingestion runtime_executor llm_gateway
```

## Installation

The CLI requires Python 3.8+ and the following packages:
- `httpx`
- `httpx-sse`

Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install httpx httpx-sse
```

## Usage

### Basic Usage

```bash
./scripts/cortex-cli --manifest path/to/agent.yml
```

### With Alias (Short Form)

```bash
./scripts/cortex-cli -m std/manifests/agents/assistant/agent.yml
```

### Custom Service URL

If services are running on a different host:
```bash
./scripts/cortex-cli -m agent.yml --url http://192.168.1.100
```

### Using the Makefile

Add to the Makefile for convenience:
```bash
make cli-chat MANIFEST=std/manifests/agents/assistant/agent.yml
```

## Features

### Chat Commands

Once in the chat interface, you can use:

- `/help` - Show available commands
- `/info` - Display agent information
- `/history` - Show conversation history
- `/clear` - Clear conversation history
- `/quit` or `/exit` - Exit the chat session

### Streaming Responses

The CLI supports real-time streaming of LLM responses, providing a responsive chat experience.

### Agent Configuration

The CLI respects all agent manifest settings:
- **Cognitive Engine**: Uses the specified provider and model
- **Temperature**: Applies configured temperature settings
- **Max Tokens**: Respects token limits
- **Persona**: Loads system prompts (if available)

## Architecture

```
┌─────────────┐
│  User Input │
└──────┬──────┘
       │
┌──────▼──────────┐
│  Cortex-CLI     │
│  (This Script)  │
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
┌──────▼───────────┐  ┌──▼──────────┐
│ Manifest         │  │ LLM Gateway │
│ Ingestion (8082) │  │   (8081)    │
└──────────────────┘  └──────┬──────┘
                             │
                      ┌──────▼─────────┐
                      │  LLM Providers │
                      │  (Gemini/etc)  │
                      └────────────────┘
```

## Example Session

```bash
$ ./scripts/cortex-cli -m std/manifests/agents/assistant/agent.yml

Checking services...
  ✓ Manifest Ingestion
  ✓ Runtime Executor
  ✓ LLM Gateway

Loading manifest: std/manifests/agents/assistant/agent.yml
✓ Loaded agent: assistant
✓ Agent session ready: cli-20251009_140800

======================================================================
  AGENT: assistant
======================================================================
  Summary: Standard general-purpose assistant with time utilities
  Version: 1.0
  State: stable
  Agency Level: default
  Model: google/gemini-1.5-flash
  Tools: 2 loaded
  Session: cli-20251009_140800
======================================================================

Chat session started. Type /help for commands or /quit to exit.

> hello!
[14:08:13] You: hello!
[14:08:13] assistant: Hello! How can I help you today?

> /quit

Goodbye!
```

## Troubleshooting

### Services Not Running

If you see:
```
✗ Not all required services are running.
```

Start the services:
```bash
cd infra && docker-compose up -d
```

### Connection Refused

Ensure services are running on the correct ports:
```bash
curl http://localhost:8082/health  # manifest_ingestion
curl http://localhost:8083/health  # runtime_executor
curl http://localhost:8081/health  # llm_gateway
```

### No LLM Response

Check that the LLM gateway has at least one provider enabled:
```bash
curl http://localhost:8081/providers
```

Make sure you have API keys configured in `infra/env/.env`:
```bash
GEMINI_API_KEY=your_key_here
ENABLE_GEMINI=true
```

## Development

### Testing Locally

```bash
cd /path/to/Cortex-Prime-MK1
source venv/bin/activate
python3 scripts/cortex-cli -m std/manifests/agents/assistant/agent.yml
```

### Adding Features

The CLI is designed to be extensible. Key areas:

1. **Message Handling**: `send_message()` method
2. **Commands**: `handle_command()` method
3. **Agent Info**: `display_agent_info()` method

## Future Enhancements

- [ ] Tool execution support
- [ ] Multi-turn conversation with tool use
- [ ] Save/load conversation sessions
- [ ] Configuration file support
- [ ] Rich terminal UI with syntax highlighting
- [ ] Tab completion for commands
- [ ] Conversation export (JSON/Markdown)

## License

Part of the Cortex-Prime MK1 project. See main repository for license details.
