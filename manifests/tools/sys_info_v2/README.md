# System Information Tool v2

**Enhanced system diagnostics with psutil**

## Overview

Enhanced tool for retrieving comprehensive system information including OS, CPU, memory, disk, and network metrics using the psutil library.

## Operations

- `get_os` - Operating system information
- `get_cpu` - CPU usage and statistics
- `get_memory` - Memory usage statistics
- `get_disk` - Disk usage and I/O stats
- `get_network` - Network interfaces and stats
- `get_all` - All system information
- `health_check` - Tool health status

## Usage

```bash
# Basic usage
python3 scripts/sys_info_v2.py '{"operation": "get_os"}'

# Detailed metrics
python3 scripts/sys_info_v2.py '{"operation": "get_cpu", "detailed": true}'

# All information
python3 scripts/sys_info_v2.py '{"operation": "get_all"}'
```

## Dependencies

Requires psutil library:
```bash
pip install -r requirements.txt
```

## Manifest

- **Path:** `tools/sys_info_v2/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Dependencies:** psutil>=5.9.0
