# 🚀 Cortex-Prime Runtime Executor Service

**"Secure, manifest-driven execution of sovereign entities."**

## Overview

The **Runtime Executor Service** is a FastAPI microservice that provides secure, sandboxed execution of manifest-defined entities (Tools, Agents, Workflows). It acts as the execution engine for the Cortex-Prime ecosystem, bridging declarative manifests to actual code execution.

## Features

### 🔒 Security First
- **Sandboxed Execution**: Secure execution with resource limits and isolation
- **Resource Limits**: Memory, CPU, and time constraints  
- **Filesystem Isolation**: Restricted file system access
- **Network Security**: Configurable network access controls

### 🏗️ Multiple Runtime Support
- **Python Executor**: Secure Python script execution with import restrictions
- **Shell Executor**: Bash/shell script execution (with security hardening)
- **Docker Executor**: Containerized execution (planned)

### 📊 Execution Management
- **Execution Registry**: Track all executions with detailed metadata
- **Resource Monitoring**: Monitor memory, CPU, and execution time
- **Cancellation Support**: Cancel long-running executions
- **Statistics & Analytics**: Execution statistics and performance metrics

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /executors` - List available runtime executors

### Execution
- `POST /execute/tool` - Execute a tool by name
- `POST /execute/agent` - Execute an agent by name  
- `POST /execute/workflow` - Execute a workflow by name
- `POST /execute/direct` - Direct execution with full request object

### Monitoring
- `GET /executions` - List recent executions with filters
- `GET /executions/{id}` - Get specific execution details
- `POST /executions/{id}/cancel` - Cancel running execution

## Usage Examples

### Execute a Tool
```bash
curl -X POST "http://localhost:8083/execute/tool" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "sys_info",
       "parameters": {
         "operation": "get_cpu"
       }
     }'
```

### Execute with Context
```bash
curl -X POST "http://localhost:8083/execute/tool" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "sys_info", 
       "parameters": {"operation": "get_memory"},
       "context": {
         "security_level": "sandboxed",
         "resource_limits": {
           "max_memory_mb": 256,
           "max_execution_time_seconds": 30
         }
       }
     }'
```

## Integration with Cortex-Prime

1. **Manifest Ingestion**: Fetches manifest definitions from the manifest ingestion service
2. **Script Resolution**: Automatically resolves script paths from manifests
3. **Parameter Handling**: Securely passes parameters to executed scripts
4. **Result Processing**: Captures and processes execution results

## Writing Compatible Scripts

### Python Scripts
```python
#!/usr/bin/env python3

# Import runtime executor utilities
from executors.python_executor import get_execution_parameters, return_result, return_error

def main():
    # Get parameters passed from the executor
    params = get_execution_parameters()
    operation = params.get('operation', 'health_check')
    
    try:
        if operation == 'get_cpu':
            import psutil
            result = {'cpu_percent': psutil.cpu_percent()}
        elif operation == 'health_check':
            result = {'status': 'ok', 'message': 'Tool is working'}
        else:
            return_error(f"Unknown operation: {operation}")
        
        # Return the result (will be JSON-serialized)
        return_result(result)
        
    except Exception as e:
        return_error(str(e), "execution_error")

if __name__ == '__main__':
    main()
```

### Tool Manifest Example
```yaml
kind: Tool
name: "cpu_monitor"
summary: "Monitor CPU usage"
implementation:
  type: "python"
  path: "./scripts/cpu_monitor.py"
parameters:
  - name: "interval"
    type: "integer"
    description: "Monitoring interval in seconds"
    default: 1
```

## Security Model

### Security Levels
- **TRUSTED**: Full system access (for verified tools)
- **SANDBOXED**: Limited system access with resource constraints  
- **ISOLATED**: Container-based execution (Docker)

### Resource Limits
- Memory limit (default: 512MB)
- CPU time limit (default: 50%)
- Execution timeout (default: 5 minutes)
- File size limits
- Network request limits

## Configuration

### Environment Variables
```bash
HOST=0.0.0.0
PORT=8083
LOG_LEVEL=info
MANIFEST_INGESTION_URL=http://manifest_ingestion:8082
```

## Architecture

```
runtime_executor/
├── main.py                    # FastAPI application
├── models/
│   └── execution_models.py    # Pydantic models for execution
├── executors/
│   ├── base_executor.py       # Base executor class
│   ├── python_executor.py     # Python script executor
│   ├── shell_executor.py      # Shell script executor
│   └── docker_executor.py     # Docker executor (planned)
├── registry/
│   └── execution_registry.py  # Execution tracking and history
└── README.md                  # This file
```

## Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py

# Test with a simple execution
curl -X POST http://localhost:8083/execute/tool \
     -H "Content-Type: application/json" \
     -d '{"tool_name": "sys_info", "parameters": {"operation": "health_check"}}'
```

## Future Enhancements

- **Docker Integration**: Full containerized execution support
- **Language Support**: Additional runtime executors (Node.js, Go, etc.)
- **Advanced Security**: SELinux/AppArmor integration
- **Distributed Execution**: Multi-node execution support
- **Performance Optimization**: Execution pooling and caching

## License

Part of the Cortex-Prime MK1 ecosystem.
**"The distance between thought and action, minimized."**