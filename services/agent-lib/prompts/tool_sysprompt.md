# AI Tool Development Specification (ATDS v1.0)

## 1. Core Architecture

### 1.1 Directory Structure
```
toolname/
├── README.md               # Documentation and usage examples
├── toolname.yml            # Tool definition and interface
├── .env.example            # Example environment configuration
├── src/                    # Source code directory
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Entry point
│   ├── core/               # Core functionality
│   │   ├── __init__.py
│   │   └── [module].py     # Core modules
│   ├── utils/              # Utility functions
│   │   └── __init__.py
│   └── adapters/           # External integrations
│       └── __init__.py
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_core.py
│   └── fixtures/           # Test data
└── docs/                   # Extended documentation
    ├── examples/           # Usage examples
    └── schemas/            # JSON schemas
```

### 1.2 Execution Model
- **Single Entrypoint**: Each tool must have a single entry point supporting positional or named arguments
- **Stateless Design**: Tools should be stateless by default, with state persisted through configurable storage
- **Exit Codes**: Use standardized exit codes (0: success, 1: error, 2: configuration error, etc.)

## 2. Configuration Framework

### 2.1 Environment Variables
- **Prefix Standard**: All environment variables must be prefixed with `TOOLNAME_` in uppercase
- **Configurability**: Every hardcoded value should be configurable via environment variables
- **Defaults**: Sensible defaults should be provided for all settings
- **Documentation**: All environment variables must be documented in `.env.example` with descriptions

### 2.2 Configuration Hierarchy
1. Command-line arguments (highest precedence)
2. Environment variables
3. Configuration files (JSON, YAML, or TOML)
4. Default values (lowest precedence)

### 2.3 Secrets Management
- **No Hardcoded Secrets**: Never include credentials in code
- **Secret Reference**: Use environment variables or secret files for credentials
- **Secret Masking**: Mask secrets in logs and error messages

## 3. Interface Standards

### 3.1 Input Protocol
- **JSON Input**: Accept structured input as JSON
- **Schema Validation**: Validate input against a JSON schema
- **Graceful Degradation**: Handle missing optional parameters gracefully

### 3.2 Output Protocol
- **JSON Output**: Structured JSON response for machine parsing
- **Status Object**: Include `success` boolean in all responses
- **Error Handling**: Standardized error format with type, message, and context
- **Pagination**: Consistent pagination format with `items`, `total`, `offset`, `limit`, and `has_more`

### 3.3 Interactive Mode
- **Human-Friendly Output**: Format output for readability when detecting interactive use
- **Progress Indicators**: Show progress for long-running operations
- **Command Help**: Provide command-specific help with examples

## 4. Documentation Requirements

### 4.1 Tool Definition (toolname.yml)
```yaml
ToolGroup:
  ToolName:
    name: "tool_name"
    description: >
      # 📚 Tool Title
      
      One-sentence description of the tool's purpose.
      
      ## 🔑 Key Features
      - Feature one with **important terms** highlighted
      - Feature two explained
      
      ## 💡 Usage Patterns
      - **Pattern Name**: Description of how to use this pattern
      - **Another Pattern**: With examples
      
      ## ⚙️ Configuration
      Brief notes on configuration options
      
    type: "script|service|app"
    runtime: "python3|node|etc"
    path: "./src/main.py"
    parameters_schema: {...}  # JSON Schema for parameters
    example_usage: [...]      # List of usage examples
    response_format: {...}    # Expected response structure
    error_handling: {...}     # Error codes and scenarios
```

### 4.2 README Structure
1. **Overview**: Purpose and capabilities
2. **Installation**: Dependencies and setup
3. **Quick Start**: Simple examples
4. **Configuration**: All configuration options
5. **Usage Examples**: Common use cases
6. **API Reference**: Complete parameter reference
7. **Error Handling**: List of errors and resolutions
8. **Performance Notes**: Optimization tips
9. **Security Considerations**: Security best practices
10. **Contributing**: Guidelines for contributors

### 4.3 Code Documentation
- **Module Docstrings**: Purpose of each module
- **Function Docstrings**: Purpose, parameters, return values, exceptions
- **Type Annotations**: Python type hints for all functions
- **Examples**: Code examples in docstrings

## 5. Error Handling & Logging

### 5.1 Error Taxonomy
- **Validation Errors**: Input validation failures
- **Resource Errors**: Missing files, databases, etc.
- **Configuration Errors**: Misconfiguration issues
- **External Service Errors**: Third-party service failures
- **Internal Errors**: Unexpected exceptions

### 5.2 Error Response Format
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Human-readable error message",
    "code": "ERROR_CODE",
    "details": {
      "field": "field_name",
      "reason": "specific reason"
    },
    "request_id": "unique_id"
  }
}
```

### 5.3 Logging Standard
- **Log Levels**: ERROR, WARNING, INFO, DEBUG
- **Log Format**: `timestamp - level - component - message - context`
- **Contextual Logging**: Include operation ID, user context
- **Sensitive Data**: Never log sensitive data or credentials

## 6. Performance & Scalability

### 6.1 Resource Management
- **Connection Pooling**: Reuse database/API connections
- **Resource Cleanup**: Close files and connections properly
- **Memory Management**: Limit in-memory processing for large datasets
- **Timeouts**: Set appropriate timeouts for all operations

### 6.2 Caching Strategy
- **Cache Layer**: Implement caching for expensive operations
- **Cache Invalidation**: Clear strategy for invalidation
- **Idempotent Operations**: Support for repeated operations

### 6.3 Concurrency
- **Thread Safety**: Thread-safe operations or document limitations
- **Rate Limiting**: Self-imposed rate limits to avoid overload
- **Backoff Strategy**: Exponential backoff for retries

## 7. Testing Requirements

### 7.1 Test Coverage
- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: Test all major workflows
- **Edge Cases**: Tests for boundary conditions
- **Error Cases**: Tests for error handling

### 7.2 Test Data
- **Fixtures**: Store test data as fixtures
- **Mocks**: Mock external dependencies
- **Parameterization**: Test multiple variants of inputs

### 7.3 Test Documentation
- **Test Purpose**: Document what each test verifies
- **Test Prerequisites**: Document required environment

## 8. Security Standards

### 8.1 Data Protection
- **Input Sanitization**: Sanitize all inputs
- **Output Encoding**: Encode all outputs
- **Sensitive Data**: Never expose sensitive data in responses

### 8.2 Access Control
- **Authentication**: Support for authentication when required
- **Authorization**: Verify permissions before operations
- **Rate Limiting**: Protect against abuse

### 8.3 Security Checklist
- No hardcoded credentials
- No sensitive data in logs
- Secure defaults for all settings
- Input validation for all parameters
- Minimal permissions principle

## 9. Interoperability

### 9.1 Tool Composition
- **Input/Output Compatibility**: Tools should be chainable
- **Standard Data Types**: Use consistent types across tools
- **Metadata Preservation**: Preserve context and metadata

### 9.2 Extension Points
- **Plugin Architecture**: Support for extensions
- **Event Hooks**: Pre/post operation hooks
- **Middleware**: Support for request/response transformation

### 9.3 Integration Interfaces
- **REST Integration**: HTTP endpoint for web integration
- **CLI Integration**: Command-line interface
- **Library Mode**: Importable as a library

## 10. Versioning & Change Management

### 10.1 Version Scheme
- **Semantic Versioning**: MAJOR.MINOR.PATCH format
- **Version Documentation**: Document changes between versions
- **Version in API**: Include version in responses

### 10.2 Backward Compatibility
- **Deprecation Policy**: Mark features as deprecated before removal
- **Compatibility Layer**: Support older formats when feasible
- **Migration Path**: Provide migration path for breaking changes

---

## Implementation Example: Data Processor Tool

To illustrate the specification, here's a minimal example of a data processor tool:

```python name=src/main.py
#!/usr/bin/env python3
"""
Data Processor - Example tool following the AI Tool Development Specification.
Processes input data according to specified transformations.
"""

import json
import os
import sys
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("DATAPROC_LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("dataproc")

# Load configuration
load_dotenv()

def get_config(key: str, default: Any) -> Any:
    """Get configuration value with fallback to default."""
    return os.getenv(f"DATAPROC_{key}", default)

def process_data(data: Dict[str, Any], transformations: List[str]) -> Dict[str, Any]:
    """
    Process data according to specified transformations.
    
    Args:
        data: Input data dictionary
        transformations: List of transformation names to apply
        
    Returns:
        Processed data dictionary
        
    Raises:
        ValueError: If an unknown transformation is requested
    """
    result = data.copy()
    
    for transform in transformations:
        if transform == "uppercase_strings":
            result = {k: v.upper() if isinstance(v, str) else v for k, v in result.items()}
        elif transform == "round_numbers":
            result = {k: round(v) if isinstance(v, (int, float)) else v for k, v in result.items()}
        else:
            raise ValueError(f"Unknown transformation: {transform}")
            
    return result

def main():
    """Main entry point with argument parsing and error handling."""
    try:
        # Parse input
        if len(sys.argv) < 2:
            print(json.dumps({
                "success": False,
                "error": {
                    "type": "InputError",
                    "message": "No input provided"
                }
            }))
            sys.exit(1)
            
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "error": {
                    "type": "ValidationError",
                    "message": f"Invalid JSON: {str(e)}"
                }
            }))
            sys.exit(1)
        
        # Validate required parameters
        if "data" not in params:
            print(json.dumps({
                "success": False,
                "error": {
                    "type": "ValidationError",
                    "message": "Missing required parameter: data"
                }
            }))
            sys.exit(1)
            
        # Process with default transformations if none specified
        transformations = params.get("transformations", [])
        
        # Process the data
        result = process_data(params["data"], transformations)
        
        # Return success response
        print(json.dumps({
            "success": True,
            "result": result,
            "transformations_applied": transformations
        }))
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(json.dumps({
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": str(e)
            }
        }))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error")
        print(json.dumps({
            "success": False,
            "error": {
                "type": "InternalError",
                "message": "An internal error occurred"
            }
        }))
        sys.exit(2)

if __name__ == "__main__":
    main()
```

```yaml name=dataproc.yml
DataTools:
  DataProcessor:
    name: "dataproc"
    description: >
      # 🔄 Data Processor
      
      Transform and process structured data with configurable operations.
      
      ## 🔑 Key Features
      - Apply multiple transformations in sequence
      - Preserve data structure during transformations
      - Extensible transformation library
      
      ## 💡 Usage Patterns
      - **Data Cleaning**: Normalize data formats before processing
      - **Format Conversion**: Transform data between different schemas
      
      ## ⚙️ Configuration
      Configurable via DATAPROC_* environment variables
      
    type: "script"
    runtime: "python3"
    path: "./src/main.py"
    parameters_schema:
      type: "object"
      properties:
        data:
          type: "object"
          description: "Input data object to process"
        transformations:
          type: "array"
          items:
            type: "string"
            enum: ["uppercase_strings", "round_numbers"]
          description: "List of transformations to apply in sequence"
      required: ["data"]
    example_usage:
      - data:
          name: "example"
          value: 123.45
        transformations: ["uppercase_strings", "round_numbers"]
    response_format:
      success:
        type: "boolean"
      result:
        type: "object"
        description: "Processed data"
      transformations_applied:
        type: "array"
        items:
          type: "string"
        description: "List of transformations that were applied"
    error_handling:
      error_types:
        - "ValidationError: Input validation failed"
        - "InternalError: Unexpected error occurred"
```

```markdown name=README.md
# Data Processor Tool

Transform and process structured data with configurable operations.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Basic usage
echo '{"data": {"name": "test", "value": 42.8}}' | python src/main.py

# With transformations
echo '{"data": {"name": "test", "value": 42.8}, "transformations": ["uppercase_strings", "round_numbers"]}' | python src/main.py
```

## Configuration

The tool supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| DATAPROC_LOG_LEVEL | Logging level (INFO, DEBUG, etc.) | INFO |

## Available Transformations

| Name | Description |
|------|-------------|
| uppercase_strings | Converts all string values to uppercase |
| round_numbers | Rounds all numeric values to integers |

## API Reference

### Input Parameters

- `data` (required): Object containing the data to process
- `transformations` (optional): Array of transformation names to apply

### Response Format

Success Response:
```json
{
  "success": true,
  "result": {
    "..." : "transformed data"
  },
  "transformations_applied": ["transformation1", "transformation2"]
}
```

Error Response:
```json
{
  "success": false,
  "error": {
    "type": "ErrorType",
    "message": "Error description"
  }
}
```

## Error Handling

| Error Type | Description |
|------------|-------------|
| ValidationError | Input validation failed or invalid transformation requested |
| InternalError | An unexpected internal error occurred |

## Security Considerations

- This tool does not handle sensitive data
- All inputs are validated before processing
```

