#!/usr/bin/env python3
"""
System Information Tool v2.0
Compatible with Cortex-Prime Runtime Executor Service

This script demonstrates the proper integration with the runtime executor.
It uses the executor utility functions to receive parameters and return results.
"""

import sys
import json
import platform
from pathlib import Path

# Add the runtime executor utilities to path (when running in executor context)
try:
    from executors.python_executor import get_execution_parameters, return_result, return_error
except ImportError:
    # Fallback for direct execution (testing)
    def get_execution_parameters():
        if len(sys.argv) > 1:
            try:
                with open(sys.argv[1], 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def return_result(result):
        print(json.dumps(result, default=str))
    
    def return_error(error_msg, error_type="execution_error"):
        print(json.dumps({"error": error_msg, "type": error_type}))
        sys.exit(1)

# Try to import psutil, handle gracefully if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_os_info():
    """Get operating system information"""
    return {
        "system": platform.system(),
        "release": platform.release(), 
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "python_version": platform.python_version()
    }


def get_cpu_info():
    """Get CPU information"""
    if not PSUTIL_AVAILABLE:
        return_error("psutil library not available for CPU info", "dependency_error")
    
    try:
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        return_error(f"Failed to get CPU info: {str(e)}")


def get_memory_info():
    """Get memory information"""
    if not PSUTIL_AVAILABLE:
        return_error("psutil library not available for memory info", "dependency_error")
    
    try:
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        
        return {
            "virtual_memory": {
                "total": virtual_mem.total,
                "available": virtual_mem.available,
                "used": virtual_mem.used,
                "percentage": virtual_mem.percent
            },
            "swap_memory": {
                "total": swap_mem.total,
                "used": swap_mem.used,
                "free": swap_mem.free,
                "percentage": swap_mem.percent
            }
        }
    except Exception as e:
        return_error(f"Failed to get memory info: {str(e)}")


def health_check():
    """Perform a health check"""
    return {
        "status": "ok",
        "message": "System info tool is working correctly",
        "tool_name": "sys_info_v2",
        "version": "1.0",
        "psutil_available": PSUTIL_AVAILABLE,
        "python_executable": sys.executable,
        "current_directory": str(Path.cwd())
    }


def main():
    """Main execution function"""
    try:
        # Get parameters from the runtime executor
        params = get_execution_parameters()
        operation = params.get('operation', 'health_check')
        
        # Route to appropriate function based on operation
        if operation == 'get_os':
            result = get_os_info()
        elif operation == 'get_cpu':
            result = get_cpu_info()
        elif operation == 'get_memory':
            result = get_memory_info()
        elif operation == 'health_check':
            result = health_check()
        else:
            return_error(f"Unknown operation: {operation}. Valid operations: get_os, get_cpu, get_memory, health_check")
        
        # Return the result to the runtime executor
        return_result({
            "success": True,
            "operation": operation,
            "data": result,
            "timestamp": platform.time() if hasattr(platform, 'time') else None
        })
        
    except Exception as e:
        return_error(f"Unexpected error in sys_info_v2: {str(e)}", "execution_error")


if __name__ == '__main__':
    main()