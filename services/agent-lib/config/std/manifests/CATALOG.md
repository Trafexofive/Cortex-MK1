# Standard Manifest Catalog

**Cortex-Prime MK1 Standard Library v1.0.0**

## Quick Reference

| Type | Name | Path | Author | State | Description |
|------|------|------|--------|-------|-------------|
| Tool | calculator | `std/manifests/tools/calculator/` | CORTEX_STD_LIB | stable | Basic arithmetic operations |
| Tool | text_analyzer | `std/manifests/tools/text_analyzer/` | CORTEX_STD_LIB | stable | Text analysis with NLP features |
| Relic | kv_store | `std/manifests/relics/kv_store/` | CORTEX_STD_LIB | stable | FastAPI + SQLite key-value store |
| Agent | assistant | `std/manifests/agents/assistant/` | CORTEX_STD_LIB | stable | General-purpose AI assistant |
| Workflow | data_pipeline | `std/manifests/workflows/data_pipeline/` | CORTEX_STD_LIB | stable | ETL data processing workflow |
| Monument | blog_platform | `std/manifests/monuments/blog_platform/` | CORTEX_STD_LIB | stable | Autonomous blogging platform |

---

## Tools (std::tools)

### calculator
**Path:** `std/manifests/tools/calculator/tool.yml`  
**Type:** Script-based (Python)  
**Runtime:** python3  
**Author:** CORTEX_STD_LIB  
**State:** stable  

**Operations:**
- `add` - Addition of two numbers
- `subtract` - Subtraction of two numbers
- `multiply` - Multiplication of two numbers
- `divide` - Division of two numbers (with zero-check)

**Parameters:**
```yaml
operation: string  # One of: add, subtract, multiply, divide
a: number         # First operand
b: number         # Second operand
```

**Returns:**
```yaml
success: boolean
result: number
error: string (optional)
```

**Files:**
- `tool.yml` - Manifest
- `scripts/calculator.py` - Implementation
- `tests/test_calculator.py` - Test suite
- `requirements.txt` - Dependencies (none)
- `README.md` - Documentation

**Example Usage:**
```bash
python3 scripts/calculator.py '{"operation": "add", "a": 5, "b": 3}'
```

**Import Path:**
```yaml
import:
  tools:
    - "path/to/std/manifests/tools/calculator/tool.yml"
```

---

### text_analyzer
**Path:** `std/manifests/tools/text_analyzer/tool.yml`  
**Type:** Script-based (Python)  
**Runtime:** python3  
**Author:** CORTEX_STD_LIB  
**State:** stable  

**Operations:**
- `analyze` - Complete text analysis
- `word_count` - Count words only
- `sentiment` - Sentiment detection only

**Parameters:**
```yaml
operation: string  # One of: analyze, word_count, sentiment
text: string      # Text to analyze
```

**Returns:**
```yaml
success: boolean
word_count: number
char_count: number
sentence_count: number
sentiment: string  # One of: positive, negative, neutral
avg_word_length: number
```

**Files:**
- `tool.yml` - Manifest
- `scripts/analyzer.py` - Implementation
- `requirements.txt` - Dependencies (none)

**Example Usage:**
```bash
python3 scripts/analyzer.py '{"operation": "analyze", "text": "This is wonderful!"}'
```

**Import Path:**
```yaml
import:
  tools:
    - "path/to/std/manifests/tools/text_analyzer/tool.yml"
```

---

## Relics (std::relics)

### kv_store
**Path:** `std/manifests/relics/kv_store/relic.yml`  
**Type:** REST API Service  
**Runtime:** Docker  
**Author:** CORTEX_STD_LIB  
**State:** stable  
**Port:** 8004  

**Service Type:** cache/storage  

**Endpoints:**
- `GET /health` - Health check
- `POST /set` - Store key-value pair
- `GET /get/{key}` - Retrieve value
- `DELETE /delete/{key}` - Delete key
- `GET /keys` - List all keys

**Storage:** SQLite (persistent)  

**Files:**
- `relic.yml` - Manifest
- `app/main.py` - FastAPI implementation
- `Dockerfile` - Container definition
- `docker-compose.yml` - Deployment
- `requirements.txt` - Python dependencies
- `README.md` - Documentation

**Deployment:**
```bash
cd std/manifests/relics/kv_store
docker-compose up -d
curl http://localhost:8004/health
```

**Example Usage:**
```bash
# Store data
curl -X POST http://localhost:8004/set \
  -H "Content-Type: application/json" \
  -d '{"key": "user_1", "value": {"name": "John"}}'

# Retrieve data
curl http://localhost:8004/get/user_1
```

**Import Path:**
```yaml
infrastructure:
  relics:
    - name: "storage"
      path: "path/to/std/manifests/relics/kv_store/relic.yml"
```

---

## Agents (std::agents)

### assistant
**Path:** `std/manifests/agents/assistant/agent.yml`  
**Type:** Conversational AI Agent  
**Author:** CORTEX_STD_LIB  
**State:** stable  
**Agency Level:** default  
**Grade:** common  

**Capabilities:**
- General-purpose conversation
- Time utilities (via local tool)
- Mathematical calculations (via external tool)
- Context-aware responses

**Local Tools:**
- `time_tool` - Date/time utilities

**External Imports:**
- `std::tools::calculator` - Arithmetic operations

**Context Feeds:**
- `current_time` - On-demand time from time_tool
- `system_info` - Periodic system status (5 min interval)

**Cognitive Engine:**
- Primary: Google Gemini 1.5 Flash
- Fallback: Ollama Llama 3.1 8B

**Files:**
- `agent.yml` - Manifest
- `system-prompts/assistant.md` - System prompt
- `tools/time_tool/` - Local time tool

**Import Path:**
```yaml
intelligence:
  agents:
    - name: "my_assistant"
      path: "path/to/std/manifests/agents/assistant/agent.yml"
```

**Extension Example:**
```yaml
kind: Agent
name: "custom_assistant"
extends: "std/manifests/agents/assistant/agent.yml"
config:
  specialization: "customer_support"
```

---

## Workflows (std::workflows)

### data_pipeline
**Path:** `std/manifests/workflows/data_pipeline/workflow.yml`  
**Type:** ETL Workflow  
**Author:** CORTEX_STD_LIB  
**State:** stable  
**Trigger:** on_demand  

**Purpose:** Extract, transform, and load data through tool and relic processing.

**Steps:**
1. Analyze text (via text_analyzer tool)
2. Store results (via kv_store relic)
3. Return confirmation

**Required Components:**
- `std::tools::text_analyzer`
- `std::relics::kv_store`

**Files:**
- `workflow.yml` - Manifest
- `README.md` - Documentation

**Import Path:**
```yaml
automation:
  workflows:
    - name: "process_data"
      path: "path/to/std/manifests/workflows/data_pipeline/workflow.yml"
```

---

## Monuments (std::monuments)

### blog_platform
**Path:** `std/manifests/monuments/blog_platform/monument.yml`  
**Type:** Complete Autonomous System  
**Author:** CORTEX_STD_LIB  
**State:** stable  
**Port:** 9001  
**Complexity:** simple  

**Architecture:**
- **Infrastructure:** 1 relic (content_store via kv_store)
- **Intelligence:** 1 agent (writing_assistant via assistant)
- **Automation:** 1 workflow (publish_pipeline via data_pipeline)

**Components:**
- `std::relics::kv_store` - Content storage
- `std::agents::assistant` - Writing assistant
- `std::workflows::data_pipeline` - Publishing pipeline

**Features:**
- Markdown support
- AI writing assistance
- Auto-tagging
- Scheduled publishing

**Limits:**
- Max posts: 1,000
- Max post size: 50KB
- Concurrent users: 10

**Files:**
- `monument.yml` - Manifest
- `docker-compose.yml` - Multi-service deployment
- `README.md` - Documentation

**Deployment:**
```bash
cd std/manifests/monuments/blog_platform
docker-compose up -d
curl http://localhost:9001/health
```

**API Endpoints:**
- `POST /posts` - Create blog post
- `GET /posts` - List all posts
- `GET /posts/{id}` - Get specific post

**Import Path:**
```yaml
# Use as reference/template for custom monuments
# Monument imports are typically used via extension
```

---

## Import Patterns

### Using Standard Tools in Custom Agent
```yaml
kind: Agent
name: "my_agent"
import:
  tools:
    - "../../std/manifests/tools/calculator/tool.yml"
    - "../../std/manifests/tools/text_analyzer/tool.yml"
```

### Using Standard Relic in Custom Monument
```yaml
kind: Monument
name: "my_platform"
infrastructure:
  relics:
    - name: "storage"
      path: "../../std/manifests/relics/kv_store/relic.yml"
      required: true
```

### Composing Standard Components
```yaml
kind: Monument
name: "data_platform"

infrastructure:
  relics:
    - name: "data_store"
      path: "std/manifests/relics/kv_store/relic.yml"

intelligence:
  agents:
    - name: "assistant"
      path: "std/manifests/agents/assistant/agent.yml"

automation:
  workflows:
    - name: "pipeline"
      path: "std/manifests/workflows/data_pipeline/workflow.yml"
```

---

## Version Information

**Library Version:** 1.0.0  
**Manifest Standard:** v1.0 Sovereign Core Standard  
**Total Components:** 6 (2 tools, 1 relic, 1 agent, 1 workflow, 1 monument)  
**Status:** Production Ready  

---

## Testing

All standard manifests include:
- ✅ Complete implementation code
- ✅ Functional tests (where applicable)
- ✅ Documentation
- ✅ Deployment configurations
- ✅ Example usage

### Test Commands

```bash
# Test calculator tool
cd std/manifests/tools/calculator
python3 scripts/calculator.py '{"operation": "add", "a": 5, "b": 3}'
python3 tests/test_calculator.py

# Test text analyzer
cd std/manifests/tools/text_analyzer
python3 scripts/analyzer.py '{"operation": "analyze", "text": "Hello world"}'

# Deploy KV store
cd std/manifests/relics/kv_store
docker-compose up -d
curl http://localhost:8004/health

# Deploy blog platform monument
cd std/manifests/monuments/blog_platform
docker-compose up -d
curl http://localhost:9001/health
```

---

## Maintenance

All standard manifests are maintained to:
- Follow v1.0 Sovereign Core Standard exactly
- Remain production-ready and stable
- Use semantic versioning
- Include comprehensive documentation
- Pass all functional tests

For issues or contributions, see main repository documentation.
