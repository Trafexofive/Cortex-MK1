#!/usr/bin/env python3
import json
import sys
import platform
import psutil

def get_os_info():
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def get_cpu_info():
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=1)
    }

def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_percent": mem.percent
    }

def health_check():
    return {"status": "ok"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No JSON parameters provided."}))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
        operation = params.get("operation")

        if operation == "get_os":
            result = get_os_info()
        elif operation == "get_cpu":
            result = get_cpu_info()
        elif operation == "get_memory":
            result = get_memory_info()
        elif operation == "health_check":
            result = health_check()
        else:
            result = {"success": False, "error": f"Unknown operation: {operation}"}
        
        print(json.dumps({"success": True, "result": result}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
