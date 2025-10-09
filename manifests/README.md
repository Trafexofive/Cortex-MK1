# Production Manifests

**Cortex-Prime MK1 Production Manifest Collection**

## Overview

This directory contains production-ready manifests for the Cortex-Prime MK1 platform. These manifests demonstrate real-world usage patterns and serve as a foundation for building autonomous AI systems.

## Structure

```
manifests/
├── tools/                    # Production tools
│   ├── sys_info/            # System information tool
│   ├── sys_info_v2/         # Enhanced system info with psutil
│   └── sentiment_analyzer/  # Sentiment analysis tool
│
├── relics/                   # Production relics (services)
│   └── kv_store/            # Key-value storage service
│
├── agents/                   # Production agents
│   ├── journaler/           # Journal management agent
│   └── research_orchestrator/ # Research coordination agent
│
├── workflow/                 # Production workflows
│   ├── journal_entry_pipeline.workflow.yml
│   ├── multi_agent_research.workflow.yml
│   └── simple_data_processing.workflow.yml
│
├── monuments/                # Complete systems
│   ├── cortex_prime_mk1/    # The system itself
│   ├── deep_search_engine/  # AI-powered search
│   └── code_forge/          # Code generation system
│
├── autoload.yml             # Auto-load configuration
└── README.md                # This file
```

## Production Components

### Tools (3)

1. **sys_info** - Basic system diagnostics
   - Operations: get_os, get_cpu, get_memory
   - State: stable
   - Path: `tools/sys_info/`

2. **sys_info_v2** - Enhanced system diagnostics with psutil
   - Operations: get_os, get_cpu, get_memory, get_disk, get_network, get_all
   - Dependencies: psutil
   - State: stable
   - Path: `tools/sys_info_v2/`

3. **sentiment_analyzer** - ML-powered sentiment analysis
   - Current: Keyword-based (simple)
   - Production: Transformer models (optional)
   - State: stable
   - Path: `tools/sentiment_analyzer/`

### Relics (1)

1. **kv_store** - Key-value storage service
   - Type: FastAPI + SQLite
   - Port: 8004
   - State: stable
   - Path: `relics/kv_store/`

### Agents (2)

1. **journaler** - Journal management agent
   - Features: Daily journals, calendar integration
   - Sub-agents: default-worker-agent
   - Local tools: calendar
   - Local relics: journal_kv_store
   - State: unstable
   - Path: `agents/journaler/`

2. **research_orchestrator** - Research coordination agent
   - Features: Web research, PDF extraction
   - Sub-agents: web_researcher
   - Local tools: pdf_extractor
   - Local relics: research_cache
   - State: stable
   - Path: `agents/research_orchestrator/`

### Workflows (3)

1. **journal_entry_pipeline** - Journal processing workflow
2. **multi_agent_research** - Multi-agent research workflow
3. **simple_data_processing** - Basic ETL workflow (stable)

### Monuments (3)

1. **cortex_prime_mk1** - The system itself as a monument
2. **deep_search_engine** - AI-powered search engine
3. **code_forge** - Autonomous code generation system (new!)

## Auto-Loading

Configure auto-load in `autoload.yml`. Uncomment production manifests to enable.

## Standards

All manifests follow v1.0 Sovereign Core Standard with:
- Complete implementations
- Relative path imports
- Full documentation

## Related

- **std/manifests/** - Standard library
- **testing/test_against_manifest/** - Test suite
- **docs/** - Documentation

---

**Version**: 1.0.0  
**Platform**: Cortex-Prime MK1
