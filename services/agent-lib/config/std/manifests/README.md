# Cortex-Prime MK1 Standard Manifests Library

**Foundation standard manifests for autonomous AI systems**

## Overview

This is the official standard library of production-ready manifest templates for Cortex-Prime MK1. These manifests serve as both reference implementations and foundational building blocks for creating autonomous AI systems.

## Philosophy

The `std::manifests` library embodies:
- **Production Quality**: Battle-tested, fully functional implementations
- **Modular Design**: Composable building blocks following fractal architecture
- **Standard Compliance**: All manifests follow v1.0 Sovereign Core Standard
- **Zero Magic**: Explicit relative path imports, no global assumptions
- **Self-Documenting**: Complete with implementation code and documentation

## Library Structure

```
std/manifests/
├── tools/              Standard tool manifests
├── relics/             Standard relic (service) manifests
├── agents/             Standard agent manifests
├── workflows/          Standard workflow manifests
├── monuments/          Standard monument (complete system) manifests
└── README.md           This file
```

## Standard Manifests

### Tools (std::tools)
Production-ready tool implementations:

- **calculator** - Arithmetic operations (add, subtract, multiply, divide)
  - Path: `std/manifests/tools/calculator/`
  - Tested: ✅
  - Use case: Mathematical computations in agents/workflows

- **text_analyzer** - Text analysis with NLP features
  - Path: `std/manifests/tools/text_analyzer/`
  - Tested: ✅
  - Use case: Content processing, sentiment analysis, statistics

### Relics (std::relics)
Production-ready service implementations:

- **kv_store** - FastAPI + SQLite key-value store
  - Path: `std/manifests/relics/kv_store/`
  - Port: 8004
  - Deployment: Docker
  - Use case: Simple persistent storage for agents/workflows

### Agents (std::agents)
Production-ready agent implementations:

- **assistant** - General-purpose AI assistant
  - Path: `std/manifests/agents/assistant/`
  - Features: Local tools, external tools, context feeds
  - Use case: Interactive assistance, task execution

### Workflows (std::workflows)
Production-ready workflow implementations:

- **data_pipeline** - ETL data processing workflow
  - Path: `std/manifests/workflows/data_pipeline/`
  - Trigger: On-demand
  - Use case: Data ingestion and transformation

### Monuments (std::monuments)
Production-ready complete system implementations:

- **blog_platform** - Autonomous blogging platform
  - Path: `std/manifests/monuments/blog_platform/`
  - Port: 9001
  - Components: 1 relic, 1 agent, 1 workflow
  - Use case: Content management with AI assistance

## Usage

### Importing Standard Manifests

All standard manifests use relative paths and can be imported from anywhere:

```yaml
# From an agent manifest
import:
  tools:
    - "../../std/manifests/tools/calculator/tool.yml"
    - "../../std/manifests/tools/text_analyzer/tool.yml"
  relics:
    - "../../std/manifests/relics/kv_store/relic.yml"
```

```yaml
# From a monument manifest
infrastructure:
  relics:
    - name: "storage"
      path: "../../std/manifests/relics/kv_store/relic.yml"
      required: true

intelligence:
  agents:
    - name: "assistant"
      path: "../../std/manifests/agents/assistant/agent.yml"
      auto_start: true
```

### Testing Standard Manifests

Each standard manifest includes:
- Implementation code
- Tests (where applicable)
- Documentation
- Deployment configuration

```bash
# Test a standard tool
cd std/manifests/tools/calculator
python3 scripts/calculator.py '{"operation": "add", "a": 5, "b": 3}'
python3 tests/test_calculator.py

# Deploy a standard relic
cd std/manifests/relics/kv_store
docker-compose up -d
curl http://localhost:8004/health

# Deploy a standard monument
cd std/manifests/monuments/blog_platform
docker-compose up -d
curl http://localhost:9001/health
```

### Extending Standard Manifests

Standard manifests are designed to be extended:

```yaml
# Your custom agent extending std assistant
kind: Agent
version: "1.0"
name: "my_custom_assistant"

# Import base functionality
extends: "../../std/manifests/agents/assistant/agent.yml"

# Add your customizations
config:
  specialization: "customer_support"
  
import:
  tools:
    - "../../std/manifests/tools/calculator/tool.yml"
    - "./my_custom_tool/tool.yml"  # Your additional tools
```

## Standards Compliance

All standard manifests follow:
- **Manifest Version**: v1.0 Sovereign Core Standard
- **Required Fields**: kind, version, name, summary, author, state
- **Import Pattern**: Relative paths only
- **Documentation**: Complete README + inline comments
- **Testing**: Functional tests where applicable
- **Deployment**: Production-ready configurations

## Quality Criteria

To be included in `std::manifests`, a manifest must:
1. ✅ Follow v1.0 Sovereign Core Standard exactly
2. ✅ Include complete working implementation
3. ✅ Use relative path imports (no magic globals)
4. ✅ Include comprehensive documentation
5. ✅ Pass all functional tests
6. ✅ Demonstrate a clear, reusable use case
7. ✅ Be production-ready (not experimental)

## Versioning

Standard manifests follow semantic versioning:
- **Major**: Breaking changes to manifest structure
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, documentation updates

Current version: **1.0.0**

## Contributing

To propose a new standard manifest:
1. Implement following v1.0 Sovereign Core Standard
2. Include complete implementation + tests + docs
3. Use relative path imports throughout
4. Submit for review demonstrating clear use case
5. Must be production-quality, not experimental

## Relationship to test_against_manifest

- `std/manifests/` - Production standard library (foundation building blocks)
- `testing/test_against_manifest/` - Comprehensive test suite (includes complex/specialized examples)

The test suite includes all standard manifests plus additional complex and specialized examples for validation purposes.

## File Count

- Tools: 2
- Relics: 1
- Agents: 1
- Workflows: 1
- Monuments: 1
- **Total Components**: 6 production-ready standard manifests

## Examples

### Building a Custom Monument from Standard Manifests

```yaml
kind: Monument
version: "1.0"
name: "my_platform"

infrastructure:
  relics:
    - name: "data_store"
      path: "../../std/manifests/relics/kv_store/relic.yml"

intelligence:
  agents:
    - name: "ai_assistant"
      path: "../../std/manifests/agents/assistant/agent.yml"

automation:
  workflows:
    - name: "process_data"
      path: "../../std/manifests/workflows/data_pipeline/workflow.yml"
```

### Composing Standard Tools in Custom Agent

```yaml
kind: Agent
version: "1.0"
name: "data_analyst"

import:
  tools:
    - "../../std/manifests/tools/calculator/tool.yml"
    - "../../std/manifests/tools/text_analyzer/tool.yml"
    
system_prompt: |
  You are a data analyst with access to standard calculation and text analysis tools.
```

## Support

For questions or issues with standard manifests:
- Review manifest documentation in respective README files
- Check implementation code in `scripts/` or `app/` directories
- See `testing/test_against_manifest/` for usage examples

## License

All standard manifests are provided as part of Cortex-Prime MK1.
