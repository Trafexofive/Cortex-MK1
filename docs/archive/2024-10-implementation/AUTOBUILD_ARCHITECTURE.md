# Tool Auto-Build System Architecture

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPER CREATES TOOL                       │
│                                                                   │
│  manifests/tools/calculator/                                     │
│  ├── tool.yml              ← Manifest defines everything         │
│  ├── scripts/                                                     │
│  │   └── calculator.py     ← Implementation                      │
│  └── requirements.txt       ← Dependencies                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              CONTAINER ORCHESTRATOR AUTO-BUILDS                  │
│                                                                   │
│  1. Read tool.yml manifest                                       │
│  2. Extract implementation spec:                                 │
│     - runtime: "python3"                                         │
│     - entrypoint: "./scripts/calculator.py"                      │
│     - build.engine: "pip"                                        │
│     - build.requirements_file: "./requirements.txt"              │
│                                                                   │
│  3. ToolBuilder.generate_dockerfile()                            │
│     ↓                                                             │
│     FROM python:3.11-slim                                        │
│     WORKDIR /tool                                                │
│     COPY requirements.txt .                                      │
│     RUN pip install -r requirements.txt                          │
│     COPY ./scripts/ ./scripts/                                   │
│     RUN chmod +x ./scripts/calculator.py                         │
│     ENTRYPOINT ["python3", "./scripts/calculator.py"]            │
│                                                                   │
│  4. Build Docker image                                           │
│  5. Tag: cortex/tool-calculator:latest                           │
│  6. Cache for future use                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   TOOL READY FOR EXECUTION                       │
│                                                                   │
│  Docker Image: cortex/tool-calculator:latest                     │
│  Status: Cached and ready                                        │
│  Execution: Ephemeral containers on-demand                       │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AGENT ORCHESTRATOR                            │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Agent requests tool execution                                  │   │
│  │   → POST /containers/tool/execute                             │   │
│  │   → { tool_name: "calculator", parameters: {...} }            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬───────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      CONTAINER ORCHESTRATOR                           │
│                                                                        │
│  ┌────────────────────┐         ┌──────────────────────────────┐    │
│  │   DockerManager    │         │       ToolBuilder            │    │
│  │                    │         │                               │    │
│  │  1. Check if image │────────→│  1. Check if image exists    │    │
│  │     exists         │         │  2. If not, build from       │    │
│  │                    │         │     manifest                  │    │
│  │  2. Execute tool   │←────────│  3. Return image tag         │    │
│  │     in container   │         │                               │    │
│  │                    │         │  Supported Runtimes:         │    │
│  │  3. Collect logs   │         │  - Python (pip)              │    │
│  │     & results      │         │  - Node (npm)                │    │
│  │                    │         │  - Go (go mod)               │    │
│  │  4. Cleanup        │         │  - Bash                      │    │
│  └────────────────────┘         └──────────────────────────────┘    │
└────────────────────────────────┬───────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                          DOCKER ENGINE                                │
│                                                                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  Tool Image 1  │  │  Tool Image 2  │  │  Tool Image 3  │  ...    │
│  │  calculator    │  │  web_search    │  │  sys_info      │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                        │
│  Ephemeral containers created on-demand, destroyed after execution   │
└──────────────────────────────────────────────────────────────────────┘
```

## Manifest Structure

```yaml
# tool.yml - Complete specification
kind: Tool
version: "1.0"
name: "calculator"
summary: "Mathematical expression evaluator"
state: "stable"

# Implementation - tells ToolBuilder how to build
implementation:
  type: "script"                    # script | binary | service
  runtime: "python3"                # python3 | node | go | bash
  entrypoint: "./scripts/calc.py"   # Entry point

  resources:                         # Runtime limits
    memory: "64M"
    timeout: 5
  
  build:                             # Build configuration
    engine: "pip"                    # pip | npm | go | custom
    requirements_file: "./requirements.txt"
  
  health_check:                      # Health check
    type: "script"
    command: "python3 ./scripts/calc.py '{\"test\": true}'"

# Parameters - defines tool interface
parameters:
  - name: "expression"
    type: "string"
    required: true
```

## ToolBuilder Logic

```python
class ToolBuilder:
    def ensure_tool_image(tool_name: str):
        """Ensure tool image exists, building if needed."""
        
        # 1. Check if image exists
        image_tag = f"cortex/tool-{tool_name}:latest"
        if image_exists(image_tag):
            return image_tag
        
        # 2. Load tool manifest
        manifest = load_manifest(tool_name)
        
        # 3. Generate Dockerfile from manifest
        dockerfile = self.generate_dockerfile(
            runtime=manifest["implementation"]["runtime"],
            entrypoint=manifest["implementation"]["entrypoint"],
            build_config=manifest["implementation"]["build"]
        )
        
        # 4. Build image
        docker_client.build(
            dockerfile=dockerfile,
            context=tool_directory,
            tag=image_tag
        )
        
        # 5. Return image tag
        return image_tag
```

## Execution Flow

```
1. Agent needs tool
      ↓
2. Request tool execution
      ↓
3. DockerManager._get_or_build_image()
      ↓
4. ToolBuilder.ensure_tool_image()
   ├─ Image exists? → Use it
   └─ Image missing? → Build from manifest
      ↓
5. Run container with tool image
      ↓
6. Execute tool with parameters
      ↓
7. Collect stdout/stderr
      ↓
8. Parse JSON result
      ↓
9. Return to agent
      ↓
10. Cleanup container
```

## Key Benefits

### For Developers
- ✅ No manual Dockerfile creation
- ✅ Just write code + YAML
- ✅ Automatic build on first use
- ✅ Cached for performance

### For System
- ✅ Declarative tool definitions
- ✅ Consistent build process
- ✅ Version control friendly
- ✅ Scalable to infinite tools

### For Security
- ✅ Container isolation
- ✅ Resource limits enforced
- ✅ No host pollution
- ✅ Ephemeral execution

## Example: Adding a New Tool

```bash
# 1. Create tool directory
mkdir -p manifests/tools/my_tool/scripts

# 2. Write implementation
cat > manifests/tools/my_tool/scripts/my_tool.py << 'EOF'
import sys, json
result = {"status": "success", "message": "It works!"}
print(json.dumps(result))
EOF

# 3. Write manifest
cat > manifests/tools/my_tool/tool.yml << 'EOF'
kind: Tool
name: "my_tool"
implementation:
  type: "script"
  runtime: "python3"
  entrypoint: "./scripts/my_tool.py"
  build:
    engine: "pip"
    requirements_file: "./requirements.txt"
parameters:
  - name: "input"
    type: "string"
    required: true
EOF

# 4. Create empty requirements
touch manifests/tools/my_tool/requirements.txt

# 5. Done! System auto-builds on first use
curl -X POST http://localhost:8086/containers/build/tool \
  -d '{"tool_name": "my_tool"}'

# Output: Successfully built cortex/tool-my_tool:latest
```

## Comparison: Before vs After

### Before (Manual)
```
1. Write tool code
2. Write requirements.txt
3. Write Dockerfile manually
4. Build: docker build -t cortex/tool-name .
5. Push to registry (optional)
6. Update orchestrator config
7. Deploy
```

### After (Auto-Build)
```
1. Write tool code
2. Write tool.yml with implementation spec
3. Done - system handles everything
```

**Lines of code saved per tool: ~15-30 (Dockerfile + build scripts)**  
**Time saved per tool: 5-15 minutes**  
**Maintenance overhead: Eliminated**

---

This auto-build system is the foundation for rapid tool development and true declarative infrastructure. No more manual Docker configuration - just define what you want in YAML, and the system builds it.
