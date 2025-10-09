# System Information Tool

**Basic system diagnostics tool**

## Overview

Retrieves basic system information including OS, CPU, and memory usage.

## Operations

- `get_os` - Operating system information
- `get_cpu` - CPU usage and statistics
- `get_memory` - Memory usage statistics
- `health_check` - Tool health status

## Usage

```bash
python3 scripts/sys_info.py '{"operation": "get_os"}'
python3 scripts/sys_info.py '{"operation": "get_cpu"}'
python3 scripts/sys_info.py '{"operation": "get_memory"}'
```

## Dependencies

Install dependencies:
```bash
pip install -r requirements.txt
```

## Manifest

- **Path:** `tools/sys_info/tool.yml`
- **Version:** 1.0
- **State:** stable
