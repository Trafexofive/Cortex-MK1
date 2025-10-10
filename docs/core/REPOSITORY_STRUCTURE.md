# Repository Structure

This document describes the organization of the Cortex-Prime-MK1 repository.

## Overview

```
Cortex-Prime-MK1/
├── docs/                   # Documentation
│   ├── blueprints/        # Design blueprints and patterns
│   ├── CHANGELOG.md       # Version history
│   ├── FEATURES.md        # Feature documentation
│   └── *.md               # Various design docs
│
├── examples/              # Usage examples and demos
│   └── demo_agent_protocol.py
│
├── infra/                 # Infrastructure configuration
│   ├── nginx/             # NGINX configs
│   ├── docker-compose.yml # Main orchestration file
│   └── settings.yml       # Global settings
│
├── scripts/               # Utility scripts
│   ├── chat.sh           # Chat interface launcher
│   ├── start_chat_test.sh
│   └── run_all_tests.py  # Test runner
│
├── services/              # Microservices
│   ├── llm_gateway/      # LLM provider abstraction
│   ├── chat_test/        # Chat test service
│   ├── api_gateway/      # API gateway
│   ├── manifest_ingestion/ # Manifest management
│   ├── runtime_executor/ # Runtime execution
│   ├── agent-lib/        # Agent library
│   ├── voice-service/    # Voice processing
│   └── web_client/       # Web UI
│
├── testing/               # Tests and test infrastructure
│   ├── benchmarking/     # Performance tests
│   ├── test_against_manifest/ # Manifest validation
│   ├── test_manifests.py # Manifest tests
│   └── test_tools.py     # Tool tests
│
├── manifests/             # Agent/Tool/Relic manifests
│   ├── agents/           # Agent definitions
│   ├── tools/            # Tool definitions
│   └── relics/           # Relic definitions
│
├── prompts/              # Prompt templates
│   └── agent_prompts/    # Agent-specific prompts
│
├── data/                 # Runtime data
│   ├── execution_cache/  # Execution cache
│   ├── manifest_cache/   # Manifest cache
│   └── uploads/          # User uploads
│
├── Makefile              # Build automation
├── README.md             # Main documentation
├── .env                  # Environment variables (local)
├── .env.template         # Environment template
└── docker-compose.yml    # Symlink to infra/docker-compose.yml

```

## Directory Purposes

### `/docs` - Documentation
All project documentation including design docs, changelogs, features, and architectural decisions.

### `/examples` - Examples & Demos
Standalone examples demonstrating how to use the system. Each example should be self-contained and runnable.

### `/infra` - Infrastructure
Infrastructure configuration files including Docker Compose, NGINX configs, and global settings. This keeps deployment configuration separate from code.

### `/scripts` - Utility Scripts
Helper scripts for development, testing, deployment, and maintenance. Should be executable and well-documented.

### `/services` - Microservices
All microservices follow a consistent structure:
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `main.py` or equivalent entry point
- Subdirectories for modules (`core/`, `models/`, etc.)
- `README.md` - Service-specific documentation

### `/testing` - Tests
All test files, test infrastructure, and benchmarking tools. Keeps tests organized and separate from main code.

### `/manifests` - Manifests
YAML/JSON manifest definitions for agents, tools, and relics. These are the declarative configurations that drive the system.

### `/prompts` - Prompt Templates
Reusable prompt templates for LLM interactions, organized by agent or function.

### `/data` - Runtime Data
Runtime-generated data, caches, and uploads. This directory should be in `.gitignore`.

## Naming Conventions

- **Services**: lowercase with underscores (e.g., `llm_gateway`)
- **Documentation**: UPPERCASE for major docs (e.g., `CHANGELOG.md`)
- **Scripts**: lowercase with underscores, `.sh` or `.py` extension
- **Configs**: lowercase with underscores or kebab-case

## File Organization Best Practices

1. **Keep root clean**: Only essential files at root level
2. **Group by function**: Related files in dedicated directories
3. **Use README files**: Each major directory should have a README
4. **Consistent structure**: All services follow same internal layout
5. **Separate concerns**: Code, config, docs, and data are separate

## Quick Reference

| Need to... | Look in... |
|------------|-----------|
| Understand a feature | `/docs/FEATURES.md` |
| See usage examples | `/examples/` |
| Configure deployment | `/infra/` |
| Run a script | `/scripts/` |
| Develop a service | `/services/<service_name>/` |
| Write a test | `/testing/` |
| Create an agent | `/manifests/agents/` |
| Check history | `/docs/CHANGELOG.md` |

## Version History

- **v2.0** (2025-01-08): Repository restructured to mirror DeepSearchStack
- **v1.0**: Initial structure
