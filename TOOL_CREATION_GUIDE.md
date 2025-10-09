# Quick Start: Creating Tools with Auto-Build

## TL;DR

No more Dockerfiles! Just create:
1. Tool script
2. YAML manifest with `implementation` spec
3. System auto-builds on first use

## Step-by-Step Guide

### 1. Create Tool Directory

```bash
mkdir -p manifests/tools/my_tool/scripts
cd manifests/tools/my_tool
```

### 2. Write Your Tool Implementation

**scripts/my_tool.py:**
```python
#!/usr/bin/env python3
import sys
import json

def main():
    # Read input (from args or stdin)
    if len(sys.argv) > 1:
        input_data = json.loads(sys.argv[1])
    else:
        input_data = json.load(sys.stdin)
    
    # Process
    result = {
        "status": "success",
        "data": input_data
    }
    
    # Output JSON to stdout
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### 3. Create Dependencies File (if needed)

**requirements.txt:**
```
requests==2.31.0
```

### 4. Write Tool Manifest

**tool.yml:**
```yaml
kind: Tool
version: "1.0"
name: "my_tool"
summary: "Brief description"
author: "YourName"
state: "stable"

description: "Detailed description of what this tool does"

returns: "JSON object with result"

implementation:
  type: "script"
  runtime: "python3"              # python3, node, go, bash
  entrypoint: "./scripts/my_tool.py"
  
  resources:
    memory: "128M"
    timeout: 30
  
  build:
    engine: "pip"                 # pip, npm, go, or omit
    requirements_file: "./requirements.txt"
  
  health_check:
    type: "script"
    command: "python3 ./scripts/my_tool.py '{\"test\": true}'"
    expected_exit_code: 0

parameters:
  - name: "input"
    type: "string"
    description: "Input parameter"
    required: true

examples:
  - description: "Example usage"
    input:
      input: "test"

tags:
  - "category"
  - "production"
```

### 5. Build the Tool

**Option A: Auto-build on first use (recommended)**
```bash
# Just use it - system builds automatically when needed
# Agent will trigger build when tool is called
```

**Option B: Build manually via API**
```bash
curl -X POST http://localhost:8086/containers/build/tool \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "my_tool"}'
```

**Option C: Check if built**
```bash
curl http://localhost:8086/containers/build/tool/my_tool/exists
```

### 6. Test the Tool

```bash
# Test the Docker image directly
docker run --rm cortex/tool-my_tool:latest \
  '{"input": "test value"}'
```

### 7. Use in an Agent

Add to agent manifest:
```yaml
import:
  tools:
    - "my_tool"
```

## Supported Runtimes

### Python
```yaml
implementation:
  runtime: "python3"
  build:
    engine: "pip"
    requirements_file: "./requirements.txt"
```

### Node.js
```yaml
implementation:
  runtime: "node"
  build:
    engine: "npm"
    requirements_file: "./package.json"  # must have package-lock.json too
```

### Go
```yaml
implementation:
  runtime: "go"
  build:
    engine: "go"  # Uses go.mod
```

### Bash
```yaml
implementation:
  runtime: "bash"
  # No build engine needed
```

## Auto-Generated Dockerfile

The system generates this automatically:

```dockerfile
FROM python:3.11-slim
WORKDIR /tool
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./scripts/ ./scripts/
RUN chmod +x ./scripts/my_tool.py
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 ./scripts/my_tool.py '{"test": true}' || exit 1
ENTRYPOINT ["python3", "./scripts/my_tool.py"]
```

## Tool Input/Output Contract

### Input
Tool receives JSON via:
- Command line argument: `sys.argv[1]`
- OR stdin: `sys.stdin`

### Output
Tool must output JSON to stdout:
```json
{
  "status": "success",
  "result": { ... },
  "error": null
}
```

### Exit Codes
- `0` - Success
- Non-zero - Error

## Common Patterns

### Web API Tool
```python
import requests

def main():
    input_data = json.loads(sys.argv[1])
    url = input_data['url']
    
    response = requests.get(url)
    result = {
        "status": "success",
        "data": response.json()
    }
    print(json.dumps(result))
```

### File Processing Tool
```python
def main():
    input_data = json.loads(sys.argv[1])
    file_path = input_data['path']
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    result = {
        "status": "success",
        "content": content
    }
    print(json.dumps(result))
```

### Async/Long Running Tool
```python
import asyncio

async def process():
    # Do work
    await asyncio.sleep(1)
    return {"result": "done"}

def main():
    result = asyncio.run(process())
    print(json.dumps(result))
```

## Troubleshooting

### Tool Won't Build
1. Check manifest syntax: `cat tool.yml | grep -A 10 implementation`
2. Verify files exist: `ls -la`
3. Check build logs: `docker logs cortex_container_orch`

### Tool Builds but Fails
1. Test manually: `docker run --rm cortex/tool-name:latest '{"test": true}'`
2. Check logs: `docker run --rm cortex/tool-name:latest '...' 2>&1`
3. Debug interactively: `docker run -it --rm cortex/tool-name:latest /bin/bash`

### Image Not Found
1. Check if built: `docker images | grep cortex/tool`
2. Rebuild: `curl -X POST localhost:8086/containers/build/tool -d '{"tool_name": "name", "force_rebuild": true}'`

## Best Practices

1. **Keep tools focused** - One tool, one job
2. **Use type hints** - Makes code clearer
3. **Add examples** - In manifest for documentation
4. **Handle errors** - Always return JSON, even on error
5. **Set timeouts** - Don't let tools run forever
6. **Resource limits** - Be conservative with memory
7. **Health checks** - Simple command that validates tool works

## Example: Real-World Tool

See `manifests/tools/calculator/` for complete example.

## That's It!

No Dockerfiles, no manual builds, no configuration. Just code + YAML.

The system handles everything else. 🚀
